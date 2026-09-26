// Starter scene — replace. Shows the core building blocks: hero morph, colours, a title chip,
// a glass card with pop/out, and a driver (pure function of t) for procedural motion.
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, sceneTitle, W, H, DURATION } from '../lib.js';
import { circle, roundRect } from '../shapes.js';

export default function s1() {
  bgTo(0, '#1a0f5c', '#0a6fa8', '#7c2bd0', 0.5, 0.01);
  morph(0.1, circle(W / 2, H * 0.45, 260), 1.0, 'expo.out');
  heroColor(0.1, '#22d3ee', '#a78bfa', '#f472b6');

  sceneTitle('01', 'Replace me', 0.4, DURATION - 1);

  const card = el('div', 'abs chip glass', null, `<span class="ico" style="color:#67e8f9">${icon('sparkles')}</span><span>Hello motion</span>`);
  place(card, W / 2, H * 0.45);
  float(card, { amp: 10, speed: 0.6, seed: 1 });
  pop(card, 0.8);

  morph(3, roundRect(W / 2, H * 0.45, 800, 500, 60), 1.0);
  out(card, DURATION - 1);
}
