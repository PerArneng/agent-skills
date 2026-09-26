import './style.css';
import gsap from 'gsap';
import { MorphSVGPlugin } from 'gsap/MorphSVGPlugin';
import { DrawSVGPlugin } from 'gsap/DrawSVGPlugin';
import { tl, drivers, drive, W, H, DURATION, mulberry32, E, prog } from './lib.js';
import { createBg } from './bg.js';

import scenes from './scenes/index.js';

gsap.registerPlugin(MorphSVGPlugin, DrawSVGPlugin);
gsap.ticker.lagSmoothing(0);

const params = new URLSearchParams(location.search);
const RENDER = params.has('render');
const PREVIEW = !RENDER;

// grain texture (seeded, deterministic)
function makeGrain() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const img = g.createImageData(256, 256);
  const r = mulberry32(7);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = r() * 255;
    img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
    img.data[i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  document.getElementById('grain').style.backgroundImage = `url(${c.toDataURL()})`;
}

function sizeStage() {
  const stage = document.getElementById('stage');
  stage.style.width = W + 'px';
  stage.style.height = H + 'px';
  const fx = document.getElementById('fx');
  fx.setAttribute('viewBox', `0 0 ${W} ${H}`);
  fx.setAttribute('width', W);
  fx.setAttribute('height', H);
  document.getElementById('world').style.transformOrigin = `${W / 2}px ${H * 0.47}px`;
  const hero = document.getElementById('hero');
  hero.setAttribute('d', `M${W / 2} ${H / 2} m-2 0 a2 2 0 1 0 4 0 a2 2 0 1 0 -4 0`);
}

async function init() {
  sizeStage();
  makeGrain();
  const renderBg = createBg(document.getElementById('bg'));

  // subtle living camera + grain jitter
  const world = document.getElementById('world');
  const grain = document.getElementById('grain');
  drive((t) => {
    const s = 1 + Math.sin(t * 0.21) * 0.012 + 0.045 * E.inOutSine(prog(t, DURATION - 2.8, DURATION))  // slow push-in on the end card;
    world.style.transform = `translate(${(Math.sin(t * 0.17) * 8).toFixed(2)}px, ${(Math.cos(t * 0.13) * 10).toFixed(2)}px) scale(${s.toFixed(4)}) rotate(${(Math.sin(t * 0.11) * 0.35).toFixed(3)}deg)`;
    const f = Math.floor(t * 30);
    grain.style.transform = `translate(${(f * 37) % 200}px, ${(f * 71) % 200}px)`;
  });
  // hero stroke gradient slowly spins (iridescence)
  const grad = document.getElementById('heroStroke');
  drive((t) => {
    grad.setAttribute('gradientTransform', `rotate(${(t * 25) % 360} 0.5 0.5)`);
  });

  scenes.forEach((s) => s());

  await document.fonts.ready;
  // initialise every tween in chronological order so reverse seeks are exact
  tl.progress(1, true).progress(0, true);

  let last = -1;
  window.seek = (t) => {
    t = Math.max(0, Math.min(DURATION, t));
    tl.seek(t, false);
    for (const d of drivers) d(t);
    renderBg(t);
    last = t;
  };
  window.STAGE = { W, H, DURATION };
  window.seek(parseFloat(params.get('t') || '0'));
  window.ready = true;

  if (PREVIEW) {
    document.body.classList.add('preview');
    const stage = document.getElementById('stage');
    const fit = () => {
      const s = Math.min(innerWidth / W, innerHeight / H);
      stage.style.transform = `translate(${(innerWidth - W * s) / 2}px, ${(innerHeight - H * s) / 2}px) scale(${s})`;
    };
    fit();
    addEventListener('resize', fit);
    if (!params.has('t')) {
      const audio = new Audio('/audio.m4a');
      const hint = document.getElementById('playhint');
      hint.classList.add('show');
      const toggle = () => {
        if (audio.paused) { audio.play(); hint.classList.remove('show'); } else { audio.pause(); hint.classList.add('show'); }
      };
      hint.onclick = toggle;
      stage.onclick = toggle;
      addEventListener('keydown', (e) => {
        if (e.code === 'Space') toggle();
        if (e.code === 'ArrowRight') audio.currentTime += 2;
        if (e.code === 'ArrowLeft') audio.currentTime -= 2;
      });
      const loop = () => {
        if (audio.currentTime !== last) window.seek(audio.currentTime);
        requestAnimationFrame(loop);
      };
      loop();
    }
  }
}
init();
