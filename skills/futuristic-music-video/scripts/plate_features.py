# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy", "pyobjc-framework-Vision; sys_platform == 'darwin'", "pyobjc-framework-Quartz; sys_platform == 'darwin'"]
# ///
"""Plate features: what is IN each still / clip, so the overlay can draw *with* the picture instead of on top of it.

  uv run plate_features.py assets/still-images/*.png assets/video-clips/*.mp4 --out assets/plate-features
  uv run plate_features.py assets/video-clips/dance-servers-fast.mp4 --debug-video video/contact-sheets/track
  (cached per file by size+mtime+version; --force recomputes; index.json is merged, not replaced)

Per plate (coordinates normalised 0..1 of the source image, y down), for an image one sample, for a video one
sample every --every seconds (t = source time):
  lines     the strongest straight segments (LSD), longest first: [[x1,y1,x2,y2,len], ...]
  vp        vanishing point {x, y, conf, lines:[indices]} from line intersections (corridors, aisles, roads)
  person    the main human (macOS Vision): bbox, silhouette polygon, face box, joints {head, neck, eyes, ears,
            hands, ...}; people[] boxes
  contours  a few long structural contours (simplified polylines) - skylines, rack edges, desks
  bright    the brightest blobs (lights, LEDs, screens): [[x, y, area], ...]

VIDEOS are made trackable here, offline, so the overlay stays a pure function of t (it only interpolates):
  - person: short detection gaps (<= --max-gap s) are interpolated, the ends held briefly (flagged "interp");
    bbox / face / joints / poly get a centred [1,2,1] smoothing; poly is resampled to POLY_N points, clockwise,
    cyclically aligned to the previous sample so it can be lerped point by point.
  - contours, lines and bright spots are TRACKED with optical flow (Lucas-Kanade, forward-backward checked):
    a contour found at 1.0 s keeps the same id and point count while the camera moves, new detections only
    join when they are not already tracked. Parallel id arrays cids / lids / bids sit next to contours / lines /
    bright (same index), and the file gets tracks: {contours: {id: [t0, t1]}, lines: {...}} so the overlay can
    pick an edge that lives through a whole cut.
  - vp is recomputed from the tracked lines (its line indices stay valid) and smoothed.
--debug-video DIR draws the interpolated features on every frame of each clip -> DIR/<name>.track.mp4 (Read it
with contact_sheet.py --video) - the check that graphics will stay locked on the dancer.
Writes <out>/<file name>.json and <out>/index.json ({source path: features}) for render_overlay.mjs (--features).
On non-mac systems the person block falls back to OpenCV's HOG detector (box only).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

VERSION = 3         # bump when the feature format changes (invalidates the cache)
WORK = 768          # analysis size (long side)
POLY_N = 64         # person silhouette points (video)
CONT_N = 48         # tracked contour points (video)
MAX_CONT, MAX_LINES = 5, 24
LK = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))


# ---------------------------------------------------------------- per-frame detection
def detect_lines(gray):
    h, w = gray.shape
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    segs = lsd.detect(cv2.GaussianBlur(gray, (3, 3), 0))[0]
    out = []
    if segs is not None:
        for x1, y1, x2, y2 in segs.reshape(-1, 4):
            L = float(np.hypot(x2 - x1, y2 - y1))
            if L > 0.06 * max(w, h):
                out.append([x1 / w, y1 / h, x2 / w, y2 / h, L / max(w, h)])
    out.sort(key=lambda s: -s[4])
    return out[:40]


def vanishing_point(out):
    """The point most (non-parallel, non-axis-aligned) lines aim at, or None."""
    cand = []
    def ang(s): return np.arctan2(s[3] - s[1], s[2] - s[0])
    use = [i for i, s in enumerate(out) if 0.15 < abs(np.sin(ang(s))) < 0.985]
    for a in range(len(use)):
        for b in range(a + 1, len(use)):
            s1, s2 = out[use[a]], out[use[b]]
            x1, y1, x2, y2 = s1[:4]; x3, y3, x4, y4 = s2[:4]
            d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(d) < 1e-6:
                continue
            px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / d
            py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / d
            if -0.3 < px < 1.3 and -0.3 < py < 1.3:
                cand.append((px, py))
    if not cand:
        return None
    best, bi, vp = -1, [], None
    for px, py in cand:
        inl = []
        for i in use:
            x1, y1, x2, y2, L = out[i][:5]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            v1 = np.array([x2 - x1, y2 - y1]); v2 = np.array([px - mx, py - my])
            c = abs(v1 @ v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
            if c > 0.995:
                inl.append(i)
        score = sum(out[i][4] for i in inl)
        if score > best:
            best, bi, vp = score, inl, (px, py)
    if vp is None or len(bi) < 3:
        return None
    return {"x": round(float(vp[0]), 4), "y": round(float(vp[1]), 4), "conf": round(float(min(1.0, best / 1.5)), 3), "lines": bi}


def contours(gray, person_mask=None):
    """Long, smooth, single-pass structural edges (skylines, rack and desk edges, floor lines): the boundaries of
    the big tonal regions at three thresholds, minus the frame border and the performer, split into open runs."""
    h, w = gray.shape
    M = max(w, h)
    b = cv2.GaussianBlur(gray, (0, 0), 3)
    otsu, _ = cv2.threshold(b, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bad = np.zeros_like(gray, np.uint8)
    if person_mask is not None:
        bad = cv2.dilate((person_mask > 0).astype(np.uint8), np.ones((15, 15), np.uint8))
    runs = []
    for thr in (otsu, np.quantile(b, 0.8), np.quantile(b, 0.25)):
        m = (b > thr).astype(np.uint8)
        m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        for c in cs:
            c = c[:, 0]
            if len(c) < 0.25 * M:
                continue
            keep = (c[:, 0] > 3) & (c[:, 0] < w - 4) & (c[:, 1] > 3) & (c[:, 1] < h - 4) & (bad[c[:, 1], c[:, 0]] == 0)
            if not keep.all():                       # start at a dropped point so runs don't wrap
                k0 = int(np.argmin(keep)); c, keep = np.roll(c, -k0, axis=0), np.roll(keep, -k0)
            idx = np.flatnonzero(np.diff(np.r_[0, keep.astype(int), 0]))
            for a0, a1 in zip(idx[::2], idx[1::2]):
                r = c[a0:a1].astype(float)
                if len(r) < 0.25 * M:
                    continue
                k = 9                                # smooth the pixel staircase along the path
                r = np.c_[np.convolve(np.pad(r[:, 0], k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), "valid"),
                          np.convolve(np.pad(r[:, 1], k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), "valid")]
                a = cv2.approxPolyDP(r.astype(np.float32).reshape(-1, 1, 2), 0.004 * M, False)[:, 0]
                if len(a) < 2:
                    continue
                L = float(np.sum(np.hypot(*np.diff(a, axis=0).T)))
                if L < 0.3 * M:
                    continue
                v = np.diff(a, axis=0); ang = np.arctan2(v[:, 1], v[:, 0])
                turn = np.abs((np.diff(ang) + np.pi) % (2 * np.pi) - np.pi)
                sharp = int((turn > 1.0).sum())      # zigzags read as noise; prefer clean edges
                runs.append((L / (1 + 0.35 * sharp), a))
    runs.sort(key=lambda x: -x[0])
    out = []
    for _, a in runs:
        A = a / [w, h]
        if any(chamfer(resample(A, 24, False), resample(np.array(o), 24, False)) < 0.03 for o in out):
            continue
        if len(A) > 120:
            A = A[np.linspace(0, len(A) - 1, 120).astype(int)]
        out.append([[round(float(x), 4), round(float(y), 4)] for x, y in A])
        if len(out) == 5:
            break
    return out


def bright(img):
    h, w = img.shape[:2]
    v = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 2]
    thr = max(200, np.quantile(v, 0.995))
    n, lab, stats, cen = cv2.connectedComponentsWithStats((v >= thr).astype(np.uint8))
    blobs = sorted([(cen[i][0] / w, cen[i][1] / h, stats[i][4] / (w * h)) for i in range(1, n) if stats[i][4] >= 6], key=lambda b: -b[2])
    return [[round(float(x), 4), round(float(y), 4), round(float(a), 5)] for x, y, a in blobs[:12]]


JOINTS = {"head": "head_joint", "neck": "neck_1_joint", "l_hand": "left_hand_joint", "r_hand": "right_hand_joint",
          "l_foot": "left_foot_joint", "r_foot": "right_foot_joint", "l_shoulder": "left_shoulder_1_joint",
          "r_shoulder": "right_shoulder_1_joint", "root": "root", "l_eye": "left_eye_joint", "r_eye": "right_eye_joint",
          "l_ear": "left_ear_joint", "r_ear": "right_ear_joint"}


def _box(b):
    return [round(b.origin.x, 4), round(1 - b.origin.y - b.size.height, 4), round(b.size.width, 4), round(b.size.height, 4)]


def person_vision(path, quality=0):
    """macOS Vision: human rectangles, faces, body pose, person segmentation mask. Returns (person | None, mask)."""
    import Quartz
    import Vision
    from Foundation import NSURL
    h = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(path)), None)
    r1 = Vision.VNDetectHumanRectanglesRequest.alloc().init()
    r1.setUpperBodyOnly_(False)
    r2 = Vision.VNDetectHumanBodyPoseRequest.alloc().init()
    r3 = Vision.VNGeneratePersonSegmentationRequest.alloc().initWithCompletionHandler_(None)
    r3.setQualityLevel_(quality)
    r4 = Vision.VNDetectFaceRectanglesRequest.alloc().init()
    h.performRequests_error_([r1, r2, r3, r4], None)
    people = [_box(o.boundingBox()) for o in r1.results() or []]
    faces = [_box(o.boundingBox()) for o in r4.results() or []]
    joints = {}
    for o in (r2.results() or [])[:1]:
        pts, _ = o.recognizedPointsForGroupKey_error_(Vision.VNHumanBodyPoseObservationJointsGroupNameAll, None)
        by = {str(k): v for k, v in pts.items()}
        for name, key in JOINTS.items():
            v = by.get(key)
            if v is not None and v.confidence() > 0.2:
                joints[name] = [round(v.location().x, 4), round(1 - v.location().y, 4)]
    mask = None
    for o in r3.results() or []:
        pb = o.pixelBuffer()
        Quartz.CVPixelBufferLockBaseAddress(pb, 0)
        w, hh, bpr = Quartz.CVPixelBufferGetWidth(pb), Quartz.CVPixelBufferGetHeight(pb), Quartz.CVPixelBufferGetBytesPerRow(pb)
        buf = Quartz.CVPixelBufferGetBaseAddress(pb).as_buffer(bpr * hh)
        mask = np.frombuffer(buf, dtype=np.uint8).reshape(hh, bpr)[:, :w].copy()
        Quartz.CVPixelBufferUnlockBaseAddress(pb, 0)

    def pick_face(bbox):
        """The face that belongs to the main person (centre inside her box), else the largest."""
        if not faces:
            return None
        if bbox:
            bx, by, bw, bh = bbox
            inside = [f for f in faces if bx <= f[0] + f[2] / 2 <= bx + bw and by <= f[1] + f[3] / 2 <= by + bh]
            if inside:
                return max(inside, key=lambda f: f[2] * f[3])
        return max(faces, key=lambda f: f[2] * f[3])

    if mask is None or (mask > 127).mean() < 0.01:
        if not people and not faces:
            return None, None
        return {"bbox": None, "poly": None, "face": pick_face(people[0] if people else None), "joints": joints, "people": people}, None
    m = (mask > 127).astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    mh, mw = m.shape
    a = cv2.approxPolyDP(c, 0.003 * max(mw, mh), True)[:, 0]
    x, y, bw, bh = cv2.boundingRect(c)
    bbox = [round(x / mw, 4), round(y / mh, 4), round(bw / mw, 4), round(bh / mh, 4)]
    person = {"bbox": bbox, "poly": [[round(float(px) / mw, 4), round(float(py) / mh, 4)] for px, py in a],
              "area": round(float(cv2.contourArea(c)) / (mw * mh), 4), "face": pick_face(bbox), "joints": joints, "people": people}
    if "head" not in joints:                       # face centre, else the top of the silhouette, as the head point
        f = person["face"]
        if f:
            joints["head"] = [round(f[0] + f[2] / 2, 4), round(f[1] + f[3] / 2, 4)]
        else:
            top = a[np.argmin(a[:, 1])]
            joints["head"] = [round(float(top[0]) / mw, 4), round(float(top[1]) / mh + 0.03, 4)]
    return person, m


def person_hog(img):
    hog = cv2.HOGDescriptor(); hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    rects, _ = hog.detectMultiScale(img, winStride=(8, 8))
    if not len(rects):
        return None
    h, w = img.shape[:2]
    x, y, bw, bh = max(rects, key=lambda r: r[2] * r[3])
    return {"bbox": [x / w, y / h, bw / w, bh / h], "poly": None, "face": None, "joints": {}, "people": []}


def analyse(path, quality=0):
    """-> (features, small gray frame, person mask at that size)"""
    img = cv2.imread(str(path))
    h, w = img.shape[:2]
    k = WORK / max(h, w)
    small = cv2.resize(img, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    person, mask = (person_vision(path, quality) if sys.platform == "darwin" else (person_hog(small), None))
    pm = cv2.resize(mask, (small.shape[1], small.shape[0])) if mask is not None else None
    lines = detect_lines(gray)
    vp = vanishing_point(lines)
    feat = {"lines": [[round(float(v), 4) for v in s] for s in lines[:MAX_LINES]], "vp": vp, "person": person,
            "contours": contours(gray, pm), "bright": bright(small)}
    return feat, gray, pm


# ---------------------------------------------------------------- temporal pass (videos)
def resample(P, n, closed):
    P = np.asarray(P, float)
    Q = np.vstack([P, P[:1]]) if closed else P
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]
    if d[-1] < 1e-9:
        return np.repeat(P[:1], n, axis=0)
    u = np.linspace(0, d[-1], n, endpoint=not closed)
    return np.c_[np.interp(u, d, Q[:, 0]), np.interp(u, d, Q[:, 1])]


def flow(g0, g1, pts_norm):
    """Lucas-Kanade with a forward-backward check. -> (new normalised points, ok mask)"""
    h, w = g0.shape
    p0 = (pts_norm * [w, h]).astype(np.float32).reshape(-1, 1, 2)
    p1, s1, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, **LK)
    pb, s2, _ = cv2.calcOpticalFlowPyrLK(g1, g0, p1, None, **LK)
    fb = np.linalg.norm((pb - p0).reshape(-1, 2), axis=1)
    p1 = p1.reshape(-1, 2)
    ok = (s1.ravel() == 1) & (s2.ravel() == 1) & (fb < 1.5) & (p1[:, 0] >= 0) & (p1[:, 0] < w) & (p1[:, 1] >= 0) & (p1[:, 1] < h)
    out = p1 / [w, h]
    if ok.any() and not ok.all():           # failed points move with the median of the good ones
        out[~ok] = pts_norm[~ok] + np.median(out[ok] - pts_norm[ok], axis=0)
    return out, ok


def track(samples, grays, key, ids_key, to_pts, from_pts, dup, cap, min_ok):
    """Generic optical-flow tracker over samples[i][key]: existing tracks are carried by flow, new detections
    join when not duplicates. Rewrites samples[i][key] and adds samples[i][ids_key]. -> {id: [t0, t1]}"""
    active, nid, spans = [], 0, {}
    for i, s in enumerate(samples):
        cur = []
        if i and s.get("seg", 0) == samples[i - 1].get("seg", 0):     # tracks never cross a cut inside the clip
            for tid, P in active:
                Q, ok = flow(grays[i - 1], grays[i], P)
                if ok.mean() >= min_ok:
                    cur.append((tid, Q))
        for d in s[key]:
            P = to_pts(d)
            if len(cur) >= cap:
                break
            if any(dup(P, Q) for _, Q in cur):
                continue
            cur.append((nid, P)); nid += 1
        s[key] = [from_pts(P) for _, P in cur]
        s[ids_key] = [tid for tid, _ in cur]
        for tid, _ in cur:
            spans.setdefault(tid, [s["t"], s["t"]])[1] = s["t"]
        active = cur
    return {str(k): v for k, v in spans.items()}


def chamfer(A, B):
    d = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    return 0.5 * (d.min(1).mean() + d.min(0).mean())


def r4(P):
    return [[round(float(x), 4), round(float(y), 4)] for x, y in P]


def line_pts(l):
    return np.array([[l[0], l[1]], [(l[0] + l[2]) / 2, (l[1] + l[3]) / 2], [l[2], l[3]]])


def line_dup(P, Q):
    a = np.linalg.norm(P - Q, axis=1).max(); b = np.linalg.norm(P - Q[::-1], axis=1).max()
    if min(a, b) < 0.025:
        return True
    v1, v2 = P[2] - P[0], Q[2] - Q[0]
    c = abs(v1 @ v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return c > 0.996 and np.linalg.norm(P[1] - Q[1]) < 0.02


def line_from(P):
    L = float(np.hypot(*(P[2] - P[0])))
    return [round(float(P[0][0]), 4), round(float(P[0][1]), 4), round(float(P[2][0]), 4), round(float(P[2][1]), 4), round(L, 4)]


def orient_cw(P):
    a = np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return P if a > 0 else P[::-1]          # y down: positive shoelace = clockwise on screen


def align(P, prev):
    """cyclic shift of P that best matches prev (same point count)"""
    best = min(range(len(P)), key=lambda k: np.sum((np.roll(P, -k, axis=0) - prev) ** 2))
    return np.roll(P, -best, axis=0)


def fill_series(vals, ts, max_gap, hold):
    """vals: list of np arrays or None at times ts. Interpolate interior gaps <= max_gap s, hold the ends <= hold s.
    -> (filled list, interp flags)"""
    n = len(vals); out = list(vals); flag = [False] * n
    have = [i for i, v in enumerate(vals) if v is not None]
    if not have:
        return out, flag
    for a, b in zip(have, have[1:]):
        if 1 < b - a and ts[b] - ts[a] <= max_gap:
            for i in range(a + 1, b):
                f = (ts[i] - ts[a]) / (ts[b] - ts[a]); out[i] = vals[a] * (1 - f) + vals[b] * f; flag[i] = True
    for i in range(0, have[0]):
        if ts[have[0]] - ts[i] <= hold:
            out[i] = vals[have[0]]; flag[i] = True
    for i in range(have[-1] + 1, n):
        if ts[i] - ts[have[-1]] <= hold:
            out[i] = vals[have[-1]]; flag[i] = True
    return out, flag


def smooth_series(vals):
    out = list(vals)
    for i in range(1, len(vals) - 1):
        if vals[i - 1] is not None and vals[i] is not None and vals[i + 1] is not None:
            out[i] = (vals[i - 1] + 2 * vals[i] + vals[i + 1]) / 4
    return out


def person_pass(samples, max_gap, hold):
    """one shot (no cuts inside): fill gaps, smooth, align silhouettes"""
    n = len(samples); ts = [s["t"] for s in samples]
    P = [s["person"] for s in samples]
    # silhouette -> POLY_N points, clockwise, cyclically aligned to the previous one (topmost point first at the start)
    polys, prev = [None] * n, None
    for i, p in enumerate(P):
        if p and p.get("poly") and len(p["poly"]) >= 3:
            Q = orient_cw(resample(p["poly"], POLY_N, True))
            Q = align(Q, prev) if prev is not None else np.roll(Q, -int(np.argmin(Q[:, 1])), axis=0)
            polys[i] = prev = Q
    series = {"poly": polys,
              "bbox": [np.array(p["bbox"], float) if p and p.get("bbox") else None for p in P],
              "face": [np.array(p["face"], float) if p and p.get("face") else None for p in P]}
    names = sorted({k for p in P if p for k in p.get("joints", {})})
    for k in names:
        series["j:" + k] = [np.array(p["joints"][k], float) if p and k in p.get("joints", {}) else None for p in P]
    filled, interp = {}, [False] * n
    for k, v in series.items():
        f, fl = fill_series(v, ts, max_gap, hold)
        filled[k] = smooth_series(f)
        if k == "bbox":
            interp = fl
    for i, s in enumerate(samples):
        if filled["bbox"][i] is None and filled["face"][i] is None:
            s["person"] = None
            continue
        p = dict(P[i] or {"people": []})
        p["bbox"] = [round(float(x), 4) for x in filled["bbox"][i]] if filled["bbox"][i] is not None else None
        p["face"] = [round(float(x), 4) for x in filled["face"][i]] if filled["face"][i] is not None else None
        p["poly"] = r4(filled["poly"][i]) if filled["poly"][i] is not None else None
        p["joints"] = {k: [round(float(v[0]), 4), round(float(v[1]), 4)] for k in names
                       for v in [filled["j:" + k][i]] if v is not None}
        if interp[i]:
            p["interp"] = True
        s["person"] = p


def temporal_pass(samples, grays, max_gap, hold):
    tracks = {}
    tracks["contours"] = track(samples, grays, "contours", "cids", lambda c: resample(c, CONT_N, False), r4,
                               lambda P, Q: chamfer(P, Q) < 0.025, MAX_CONT, 0.6)
    tracks["lines"] = track(samples, grays, "lines", "lids", line_pts, line_from, line_dup, MAX_LINES, 0.67)
    # bright spots: nearest-neighbour ids (they blink, flow is pointless)
    prev, nid = [], 0
    for i, s in enumerate(samples):
        if i and s["seg"] != samples[i - 1]["seg"]:
            prev = []
        ids = []
        for b in s["bright"]:
            near = [(np.hypot(b[0] - q[0], b[1] - q[1]), qid) for q, qid in prev if qid not in ids]
            m = min(near) if near else None
            if m and m[0] < 0.04:
                ids.append(m[1])
            else:
                ids.append(nid); nid += 1
        s["bids"] = ids
        prev = list(zip(s["bright"], ids))
    # vp from the tracked lines (indices stay valid), then smoothed
    for s in samples:
        s["vp"] = vanishing_point(s["lines"])
    for i in range(1, len(samples) - 1):
        a, b, c = samples[i - 1]["vp"], samples[i]["vp"], samples[i + 1]["vp"]
        if a and b and c and samples[i - 1]["seg"] == samples[i]["seg"] == samples[i + 1]["seg"]:
            b["sx"], b["sy"] = (a["x"] + 2 * b["x"] + c["x"]) / 4, (a["y"] + 2 * b["y"] + c["y"]) / 4
    for s in samples:
        if s["vp"] and "sx" in s["vp"]:
            s["vp"]["x"], s["vp"]["y"] = round(s["vp"].pop("sx"), 4), round(s["vp"].pop("sy"), 4)
    for seg in sorted({s["seg"] for s in samples}):
        person_pass([s for s in samples if s["seg"] == seg], max_gap, hold)
    return tracks


def shot_cuts(path):
    """frame indices where the clip itself hard-cuts (Veo sometimes cuts mid-clip). -> (cuts, fps, nframes)"""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    tiny, d = None, []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (96, 54), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(float)
        d.append(np.abs(g - tiny).mean() if tiny is not None else 0.0)
        tiny = g
    cap.release()
    d = np.array(d); cuts = []
    for i in range(1, len(d)):
        loc = np.r_[d[max(1, i - 6):i], d[i + 1:i + 7]]
        if d[i] > 18 and d[i] > 4 * (np.median(loc) if len(loc) else 0) + 4:
            cuts.append(i)
    return cuts, fps, len(d)


# ---------------------------------------------------------------- interpolation (mirrors the overlay's sampleAt)
def sample_at(d, st):
    S = d["samples"]
    if len(S) == 1:
        return S[0]
    st = st % d.get("duration", S[-1]["t"])
    i = max(0, min(len(S) - 2, int(np.searchsorted([s["t"] for s in S], st, side="right")) - 1))
    a, b = S[i], S[i + 1]
    f = min(1.0, max(0.0, (st - a["t"]) / max(1e-6, b["t"] - a["t"])))
    if a.get("seg", 0) != b.get("seg", 0):      # a cut inside the clip: no interpolation across it
        return a if st < b["t"] else b
    L = lambda x, y: [x[k] * (1 - f) + y[k] * f for k in range(len(x))]
    out = {"t": st, "vp": a["vp"], "lines": a["lines"], "bright": a["bright"]}
    pa, pb = a["person"], b["person"]
    if pa and pb:
        p = {"joints": {k: L(pa["joints"][k], pb["joints"][k]) for k in pa["joints"] if k in pb["joints"]}}
        for k in ("bbox", "face"):
            p[k] = L(pa[k], pb[k]) if pa.get(k) and pb.get(k) else (pa.get(k) if f < 0.5 else pb.get(k))
        p["poly"] = [L(x, y) for x, y in zip(pa["poly"], pb["poly"])] if pa.get("poly") and pb.get("poly") else pa.get("poly")
        out["person"] = p
    else:
        out["person"] = pa if f < 0.5 else pb
    cb = dict(zip(b.get("cids", []), b["contours"]))
    out["contours"] = [[L(x, y) for x, y in zip(c, cb[i])] if i in cb else c for c, i in zip(a["contours"], a.get("cids", []))]
    out["cids"] = a.get("cids", [])
    return out


def debug_video(src, d, dst):
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    k = 960 / max(w, h)
    ow, oh = int(w * k) // 2 * 2, int(h * k) // 2 * 2
    tmp = str(dst) + ".tmp.mp4"
    vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), fps, (ow, oh))
    P = lambda x, y: (int(x * ow), int(y * oh))
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        fr = cv2.resize(fr, (ow, oh))
        s = sample_at(d, i / fps)
        for c, cid in zip(s["contours"], s["cids"]):
            col = [(255, 200, 0), (0, 200, 255), (255, 0, 200), (0, 255, 120), (200, 200, 200)][cid % 5]
            cv2.polylines(fr, [np.array([P(*q) for q in c], np.int32)], False, col, 2)
            cv2.putText(fr, f"c{cid}", P(*c[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)
        p = s["person"]
        if p:
            if p.get("poly"):
                cv2.polylines(fr, [np.array([P(*q) for q in p["poly"]], np.int32)], True, (255, 255, 0), 1)
            if p.get("bbox"):
                x, y, bw, bh = p["bbox"]; cv2.rectangle(fr, P(x, y), P(x + bw, y + bh), (0, 255, 255), 2)
            if p.get("face"):
                x, y, fw, fh = p["face"]
                cv2.circle(fr, P(x + fw / 2, y + fh / 2), int(max(fw * ow, fh * oh) * 0.75), (0, 0, 255), 2)
            for name, q in p["joints"].items():
                cv2.circle(fr, P(*q), 4, (0, 255, 0), -1)
        cv2.putText(fr, f"{i / fps:5.2f}s", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        vw.write(fr); i += 1
    vw.release(); cap.release()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(dst)], check=True)
    Path(tmp).unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="assets/plate-features")
    ap.add_argument("--every", type=float, default=0.2, help="video sampling interval (s); 0.2 tracks a dancer smoothly")
    ap.add_argument("--max-gap", type=float, default=1.0, help="interpolate person detection gaps up to this long (s)")
    ap.add_argument("--hold", type=float, default=0.6, help="hold the first/last detection this long at clip ends (s)")
    ap.add_argument("--debug-video", help="write <dir>/<name>.track.mp4 with the tracked features drawn")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    idx_path = out / "index.json"
    index = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    index = {k: v for k, v in index.items() if Path(k).exists()}      # merge: keep earlier runs' plates
    for f in map(Path, a.files):
        dst = out / (f.name + ".json")
        is_img = f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        sig = f"{f.stat().st_size}-{int(f.stat().st_mtime)}-v{VERSION}" + ("" if is_img else f"-e{a.every}")
        d = None
        if dst.exists() and not a.force:
            d = json.loads(dst.read_text())
            if d.get("sig") != sig:
                d = None
        if d is None:
            if is_img:
                img = cv2.imread(str(f)); h, w = img.shape[:2]
                feat, _, _ = analyse(f)
                d = {"src": str(f), "sig": sig, "kind": "image", "w": w, "h": h, "samples": [{"t": 0.0, **feat}]}
            else:
                probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                    "stream=width,height:format=duration", "-of", "json", str(f)], capture_output=True, text=True).stdout)
                w, h = probe["streams"][0]["width"], probe["streams"][0]["height"]
                dur = float(probe["format"]["duration"])
                cuts, fps, nfr = shot_cuts(f)
                # a sample every --every s, plus the last frame before and the first frame after each internal cut
                want = sorted({min(nfr - 1, round(k * a.every * fps)) for k in range(int(nfr / fps / a.every) + 1)}
                              | {c - 1 for c in cuts} | set(cuts))
                samples, grays = [], []
                with tempfile.TemporaryDirectory() as td:
                    cap = cv2.VideoCapture(str(f)); i = 0; W = set(want)
                    while True:
                        ok, fr = cap.read()
                        if not ok:
                            break
                        if i in W:
                            cv2.imwrite(f"{td}/f_{i:05d}.png", fr)
                        i += 1
                    cap.release()
                    for i in want:
                        feat, gray, _ = analyse(Path(f"{td}/f_{i:05d}.png"), quality=1)
                        samples.append({"t": round(i / fps, 4), "seg": sum(1 for c in cuts if c <= i), **feat}); grays.append(gray)
                tracks = temporal_pass(samples, grays, a.max_gap, a.hold)
                d = {"src": str(f), "sig": sig, "kind": "video", "w": w, "h": h, "duration": dur, "every": a.every,
                     "cuts": [round(c / fps, 4) for c in cuts], "tracks": tracks, "samples": samples}
            dst.write_text(json.dumps(d))
        index[str(f)] = d
        if a.debug_video and d["kind"] == "video":
            dv = Path(a.debug_video); dv.mkdir(parents=True, exist_ok=True)
            debug_video(f, d, dv / (f.stem + ".track.mp4"))
        S = d["samples"]; s0 = S[0]
        if d["kind"] == "video":
            np_ = sum(1 for s in S if s["person"] and s["person"].get("bbox"))
            nf = sum(1 for s in S if s["person"] and s["person"].get("face"))
            long_c = sum(1 for t0, t1 in d["tracks"]["contours"].values() if t1 - t0 >= 2)
            print(f"{f.name:28s} video {len(S)} samples  cuts {d['cuts']}  person {np_}/{len(S)}  face {nf}/{len(S)}"
                  f"  contour tracks {len(d['tracks']['contours'])} ({long_c} >= 2 s)  line tracks {len(d['tracks']['lines'])}")
        else:
            print(f"{f.name:28s} lines {len(s0['lines']):2d}  vp {('%.2f,%.2f c%.2f' % (s0['vp']['x'], s0['vp']['y'], s0['vp']['conf'])) if s0['vp'] else '-':18s}"
                  f"  person {'yes' if s0['person'] and s0['person'].get('poly') else ('box' if s0['person'] else '-'):3s}"
                  f"  face {'yes' if s0['person'] and s0['person'].get('face') else '-':3s}"
                  f"  contours {len(s0['contours'])}  bright {len(s0['bright'])}")
    idx_path.write_text(json.dumps(index))
    print(f"wrote {idx_path} ({len(index)} plates)")


if __name__ == "__main__":
    main()
