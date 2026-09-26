// Top-left section title for the flat theme (pairs with flat-brand.css `.title` rules): mono eyebrow
// "01 ── PART 01 / 05" + large heading with a per-character reveal. Paste into src/lib.js and use it instead of
// the default centred glass pill: `sceneTitle('02', 'Role-Bound Architecture', 32.58, 45.9)`.
// Main content then lives in the left ~70% of a 1920×1080 stage (title block ends at y ≈ 190).
export function sceneTitle(num, name, tIn, tOut, { total = '05', word = 'Part', x = 100, y = 92 } = {}) {
  const w = el('div', 'abs title');
  w.innerHTML = `<div class="row1"><span class="num">${num}</span><span class="bar"></span><span class="of">${word.toUpperCase()} ${num} / ${total}</span></div><span class="name">${name
    .split('')
    .map((c) => `<span class="ch">${c === ' ' ? '&nbsp;' : c}</span>`)
    .join('')}</span>`;
  gsap.set(w, { x: x - 30, y, opacity: 0 });
  tl.to(w, { opacity: 1, x, duration: 0.9, ease: 'expo.out' }, tIn);
  const bar = w.querySelector('.bar');
  gsap.set(bar, { scaleX: 0 });
  tl.to(bar, { scaleX: 1, duration: 0.7, ease: 'expo.out' }, tIn + 0.1);
  const chars = w.querySelectorAll('.ch');
  gsap.set(chars, { opacity: 0, yPercent: 70 });
  tl.to(chars, { opacity: 1, yPercent: 0, duration: 0.55, stagger: 0.016, ease: 'power3.out' }, tIn + 0.15);
  tl.to(w, { opacity: 0, x: x - 40, filter: 'blur(10px)', duration: 0.5, ease: 'power2.in' }, tOut);
  return w;
}
