// 0.0 – 6.5  "Modern AI is probabilistic and prone to hallucination, making human oversight mandatory."
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, hash, env, gsap } from '../lib.js';
import { bubble, circle, roundRect } from '../shapes.js';

export default function s1() {
  bgTo(0, '#1a0f5c', '#0a6fa8', '#7c2bd0', 0.5, 0.01);

  // hero: dot → speech bubble
  gsap.set('#heroG', { opacity: 0 });
  tl.to('#heroG', { opacity: 1, duration: 0.4 }, 0);
  morph(0.05, circle(540, 860, 120), 0.35, 'power2.out');
  morph(0.4, bubble(540, 840, 820, 440, 70), 0.9, 'expo.out');

  // ambient little chat bubbles with typing dots
  const small = [
    [230, 470, 250, 0.2], [860, 560, 210, 0.45], [250, 1300, 230, 0.7], [860, 1240, 190, 0.95],
  ];
  const smalls = small.map(([x, y, w, t], i) => {
    const b = el('div', 'abs glass');
    b.style.cssText += `width:${w}px;height:${w * 0.46}px;border-radius:${w * 0.23}px;display:flex;gap:14px;align-items:center;justify-content:center`;
    b.innerHTML = '<i></i><i></i><i></i>';
    b.querySelectorAll('i').forEach((d) => (d.style.cssText = 'width:16px;height:16px;border-radius:50%;background:#e9e5ff;display:block'));
    place(b, x, y);
    float(b, { amp: 14, speed: 0.6, seed: i * 3 });
    pop(b, t, { dur: 0.8 });
    const dots = b.querySelectorAll('i');
    drive((tt) => dots.forEach((d, k) => (d.style.opacity = (0.35 + 0.65 * Math.max(0, Math.sin(tt * 7 - k * 0.9))).toFixed(2))));
    return b;
  });

  // AI answer label
  const ai = el('div', 'abs chip glass', null, `<span class="ico" style="color:#c4b5fd">${icon('sparkles')}</span><span>AI answer</span>`);
  place(ai, 540, 560);
  pop(ai, 0.6);

  // equation
  const eq = el('div', 'abs');
  eq.style.cssText = 'font:700 124px/1 var(--mono);white-space:nowrap;display:flex;gap:30px;align-items:center';
  eq.innerHTML = `<span class="a">10</span><span class="a" style="color:#a5b4fc">×</span><span class="a">5</span><span class="a" style="color:#a5b4fc">=</span><span class="r" style="position:relative">100<i class="strike"></i></span>`;
  place(eq, 540, 830);
  const parts = eq.querySelectorAll('.a');
  const res = eq.querySelector('.r');
  gsap.set(parts, { opacity: 0, y: 40, filter: 'blur(10px)' });
  tl.to(parts, { opacity: 1, y: 0, filter: 'blur(0px)', stagger: 0.14, duration: 0.6, ease: 'expo.out' }, 0.6);
  gsap.set(res, { opacity: 0, scale: 1.6, filter: 'blur(14px)', color: '#67e8f9' });
  tl.to(res, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.6, ease: 'expo.out' }, 2.05);

  // hallucination glitch @3.04
  tl.to(res, { color: '#ff4d6d', duration: 0.2 }, 3.0);
  heroColor(3.0, '#ff4d6d', '#f97316', '#e11d48', 0.5);
  bgTo(3.0, '#3a0a2a', '#7a1236', '#b3264a', 0.9, 0.8);
  drive((t) => {
    const g = env(t, 3.0, 4.4, 0.05, 0.3);
    if (g <= 0.001) { res.style.textShadow = 'none'; res.style.translate = '0px 0px'; return; }
    const f = Math.floor(t * 30);
    const dx = (hash(f) - 0.5) * 26 * g, dy = (hash(f + 99) - 0.5) * 10 * g;
    res.style.textShadow = `${(-8 * g + dx).toFixed(1)}px 0 rgba(34,211,238,.85), ${(8 * g - dx).toFixed(1)}px 0 rgba(255,0,110,.85)`;
    res.style.translate = `${dx.toFixed(1)}px ${dy.toFixed(1)}px`;
  });
  const warn = el('div', 'abs ico');
  warn.style.cssText += 'width:130px;height:130px;color:#ffd166;filter:drop-shadow(0 0 24px rgba(255,80,80,.9))';
  warn.innerHTML = icon('alert', 2.2);
  place(warn, 880, 650);
  pop(warn, 3.05, { ease: 'back.out(3)' });
  float(warn, { amp: 6, speed: 1.2, seed: 5, rot: 6 });

  // "hallucination" tag
  const tag = el('div', 'abs chip', null, `<span>Hallucination</span>`);
  tag.style.cssText += 'background:rgba(255,77,109,.18);border:1.5px solid rgba(255,77,109,.7);color:#ffb3c1;font-family:var(--mono);font-size:30px';
  place(tag, 540, 990);
  pop(tag, 3.25);

  // human oversight @4.36 – scanning beam + strike
  const beam = el('div', 'abs');
  beam.style.cssText = 'width:760px;height:6px;border-radius:6px;background:linear-gradient(90deg,transparent,#67e8f9,transparent);box-shadow:0 0 30px 8px rgba(103,232,249,.6)';
  place(beam, 540, 700, { opacity: 0 });
  tl.to(beam, { opacity: 1, duration: 0.15 }, 4.3);
  tl.to(beam, { y: 960, duration: 0.9, ease: 'sine.inOut', yoyo: true, repeat: 1 }, 4.3);
  tl.to(beam, { opacity: 0, duration: 0.2 }, 6.0);
  const strike = res.querySelector('.strike');
  strike.style.cssText = 'position:absolute;left:-6%;top:52%;height:10px;width:112%;background:#fff;border-radius:6px;box-shadow:0 0 18px #fff;transform-origin:0 50%';
  gsap.set(strike, { scaleX: 0 });
  tl.to(strike, { scaleX: 1, duration: 0.45, ease: 'power3.inOut' }, 5.0);

  const human = el('div', 'abs chip glass', null, `<span class="ico" style="color:#67e8f9">${icon('scanEye')}</span><span>Human oversight</span>`);
  place(human, 540, 1170);
  pop(human, 4.4);

  // MANDATORY stamp @5.42
  const stamp = el('div', 'abs');
  stamp.style.cssText = 'font:800 60px/1 var(--head);letter-spacing:.12em;color:#fff;padding:22px 36px;border:6px solid #fff;border-radius:18px;background:rgba(255,255,255,.06);box-shadow:0 0 50px rgba(255,255,255,.35)';
  stamp.textContent = 'MANDATORY';
  place(stamp, 540, 1350, { opacity: 0, scale: 2.4, rotation: -8, filter: 'blur(8px)' });
  tl.to(stamp, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.35, ease: 'power4.in' }, 5.3);
  heroColor(5.2, '#67e8f9', '#a78bfa', '#f472b6', 0.8);

  // exit
  out([...smalls, ai, eq, warn, tag, human, stamp], 6.25, { dur: 0.55, stagger: 0.02, scale: 0.7, blur: 20 });
}
