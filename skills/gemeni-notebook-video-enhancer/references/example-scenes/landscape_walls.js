// 59.4–71.8  04 AI-SMS integration: "The system plugs directly into an airline's existing safety management
// system. Safety controls aren't just suggestions. They are literal structural walls the AI cannot bypass."
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, sceneTitle, stamp, gsap, prog, lerp, E, env } from '../lib.js';
import { roundRect, shield } from '../shapes.js';

export default function s7() {
  sceneTitle('04', 'AI-SMS Integration', 59.38, 71.55);
  morph(59.2, roundRect(700, 590, 1180, 480, 30), 1.1);

  // ---- SMS panel (socket) ----
  const sms = el('div', 'abs panel');
  sms.style.cssText += 'width:500px;padding:28px 30px;display:flex;flex-direction:column;gap:12px;z-index:2';
  sms.innerHTML = `<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
      <span class="ico" style="width:32px;height:32px;color:var(--glow)">${icon('shield-check', 1.8)}</span>
      <span class="label">Airline SMS</span><span class="tag" style="margin-left:auto;color:var(--n-300);border:1.5px solid var(--line)">Existing</span></div>` +
    ['Hazard register', 'Risk controls', 'Safety policy', 'Occurrence reports'].map((r) =>
      `<div class="mono" style="font-size:19px;padding:12px 14px;border-radius:8px;background:rgba(255,255,255,.05);color:var(--fog)">${r}</div>`).join('');
  place(sms, 960, 590);
  pop(sms, 60.3, { scale: 0.9, ease: 'expo.out' });
  // socket notch on the left edge
  const sock = el('div', 'abs');
  sock.style.cssText += 'width:26px;height:120px;border-radius:6px;background:#02080f;border:2px solid rgba(255,160,92,.7);z-index:3';
  place(sock, 710, 590);
  pop(sock, 60.45);

  // ---- Airflow module slides in ("plugs directly") ----
  const mod = el('div', 'abs panel hi');
  mod.style.cssText += 'width:300px;height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;z-index:3';
  mod.innerHTML = `<span class="ico" style="width:62px;height:62px;color:var(--electric)">${icon('bot', 1.5)}</span>
    <span class="label">Airflow agent</span>`;
  place(mod, 210, 590, { opacity: 0 });
  tl.to(mod, { opacity: 1, duration: 0.5 }, 60.6);
  tl.to(mod, { x: 540, duration: 0.8, ease: 'power3.in' }, 62.3);
  tl.to(mod, { x: 530, duration: 0.25, ease: 'power2.out' }, 63.1);
  const plug = el('div', 'abs');
  plug.style.cssText += 'width:26px;height:110px;border-radius:4px;background:var(--electric);z-index:2';
  place(plug, 210 + 160, 590, { opacity: 0 });
  tl.to(plug, { opacity: 1, duration: 0.5 }, 60.6);
  tl.to(plug, { x: 700, duration: 0.8, ease: 'power3.in' }, 62.3);
  tl.to(plug, { x: 690, duration: 0.25, ease: 'power2.out' }, 63.1);
  const flash = el('div', 'abs');
  flash.style.cssText += 'width:60px;height:60px;border-radius:50%;background:radial-gradient(circle,#fff,rgba(106,244,249,0) 70%);z-index:4';
  place(flash, 710, 590, { opacity: 0, scale: 0.3 });
  tl.to(flash, { opacity: 1, scale: 5, duration: 0.15 }, 63.1);
  tl.to(flash, { opacity: 0, duration: 0.6 }, 63.25);
  tl.to(sock, { borderColor: '#6af4f9', duration: 0.2 }, 63.1);
  const con = el('div', 'abs tag', null, 'Connected');
  con.style.cssText += 'color:#001629;background:var(--green);z-index:4';
  place(con, 710, 430);
  pop(con, 63.3);
  // "safety management system": rows light up
  [...sms.querySelectorAll('.mono')].forEach((r, i) => tl.to(r, { backgroundColor: 'rgba(25,162,174,.22)', duration: 0.3 }, 64.6 + i * 0.12));

  // clear the plug assembly for the walls
  out([mod, plug, sock, sms, con], 65.8, { dur: 0.5, stagger: 0.03 });

  // ---- suggestions (sticky notes) that get dismissed ----
  const notes = ['Please avoid storm cells', 'Try to respect duty limits', 'Consider the MEL'].map((txt, i) => {
    const n = el('div', 'abs panel', null, `<span style="font:italic 500 26px/1.2 var(--head);color:var(--glow)">"${txt}"</span>`);
    n.style.cssText += 'padding:20px 26px;border-style:dashed;border-color:rgba(255,160,92,.5);white-space:nowrap';
    place(n, [460, 900, 690][i], [420, 520, 700][i], { rotation: [-4, 3, -2][i] });
    return n;
  });
  pop(notes, 66.1, { stagger: 0.14, scale: 0.8 });
  tl.to(notes, { y: '+=140', opacity: 0, rotation: '+=14', filter: 'blur(8px)', duration: 0.7, stagger: 0.08, ease: 'power2.in' }, 67.45);
  const sug = el('div', 'abs tag', null, 'Just suggestions?');
  sug.style.cssText += 'color:var(--n-300);border:1.5px solid var(--line)';
  place(sug, 700, 860);
  pop(sug, 66.9);
  out(sug, 67.6);

  // ---- structural walls ----
  heroColor(68.6, '#15a2ae', '#6af4f9', '#ffa05c', 0.6);
  morph(68.6, shield(820, 590, 380, 470), 1.0);
  const ai = el('div', 'abs panel hi');
  ai.style.cssText += 'width:170px;height:170px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px';
  ai.innerHTML = `<span class="ico" style="width:56px;height:56px;color:var(--electric)">${icon('bot', 1.5)}</span><span class="eyebrow" style="font-size:14px;color:var(--fog)">AI agent</span>`;
  place(ai, 330, 590);
  pop(ai, 68.1);
  const bad = el('div', 'abs panel');
  bad.style.cssText += 'padding:18px 22px;display:flex;align-items:center;gap:12px;border-color:rgba(255,77,94,.55)';
  bad.innerHTML = `<span class="ico" style="width:30px;height:30px;color:var(--red)">${icon('triangle-alert', 1.8)}</span><span class="label" style="font-size:24px">Unsafe action</span>`;
  place(bad, 1170, 590);
  pop(bad, 68.3);
  const walls = [0, 1, 2].map((i) => {
    const w = el('div', 'abs');
    w.style.cssText += `width:${i === 1 ? 34 : 22}px;height:420px;border-radius:6px;transform-origin:50% 100%;z-index:2;` +
      'background:repeating-linear-gradient(135deg,#ffa05c 0 14px,#ff791a 14px 28px);box-shadow:0 0 30px rgba(255,121,26,.35)';
    place(w, 760 + i * 60, 590, { scaleY: 0 });
    tl.to(w, { scaleY: 1, duration: 0.45, ease: 'back.out(1.6)' }, 68.85 + i * 0.1);
    return w;
  });
  // the AI's attempt: a packet runs at the wall and bounces
  const pk = el('div', 'abs');
  pk.style.cssText += 'width:26px;height:26px;border-radius:50%;background:var(--electric);box-shadow:0 0 20px 6px rgba(106,244,249,.6);z-index:3';
  drive((t) => {
    if (t < 69.95 || t > 71.2) return (pk.style.display = 'none');
    pk.style.display = 'block';
    const go = E.inCubic(prog(t, 69.95, 70.45)), back = E.outCubic(prog(t, 70.45, 71.0));
    const x = lerp(lerp(420, 735, go), 520, back);
    pk.style.transform = `translate(${x.toFixed(1)}px,590px) translate(-50%,-50%)`;
    pk.style.opacity = (1 - prog(t, 70.8, 71.2)).toFixed(3);
  });
  drive((t) => {
    const f = env(t, 70.42, 71.2, 0.03, 0.6);
    walls.forEach((w) => (w.style.boxShadow = `0 0 ${(30 + f * 70).toFixed(1)}px rgba(255,${(121 + f * 120).toFixed(0)},${(26 + f * 200).toFixed(0)},${(0.35 + f * 0.55).toFixed(2)})`));
  });
  const blk = el('div', 'abs stamp', null, 'BLOCKED');
  blk.style.cssText += 'color:var(--red);z-index:4;background:rgba(0,22,41,.85)';
  place(blk, 820, 350);
  stamp(blk, 70.5, -5);

  out([ai, bad, ...walls, blk], 71.5, { dur: 0.5, stagger: 0.03 });
}
