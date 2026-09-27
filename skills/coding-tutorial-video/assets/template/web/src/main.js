import './style.css';
import gsap from 'gsap';
import { MorphSVGPlugin } from 'gsap/MorphSVGPlugin';
import { DrawSVGPlugin } from 'gsap/DrawSVGPlugin';
import { tl, drivers, W, H, setData } from './lib.js';

gsap.registerPlugin(MorphSVGPlugin, DrawSVGPlugin);
gsap.ticker.lagSmoothing(0);

const params = new URLSearchParams(location.search);
const EP = params.get('ep') || 'ep1';
const RENDER = params.has('render');
const DATA = import.meta.glob('./data/ep*.json', { eager: true, import: 'default' });
const EPISODES = import.meta.glob('./episodes/ep*.js');

function sizeStage() {
  const stage = document.getElementById('stage');
  stage.style.width = W + 'px';
  stage.style.height = H + 'px';
}

async function init() {
  sizeStage();
  const data = DATA[`./data/${EP}.json`];
  setData(data);
  const build = (await EPISODES[`./episodes/${EP}.js`]()).default;
  await document.fonts.ready;
  build();
  // initialise every tween in chronological order so reverse seeks are exact
  tl.progress(1, true).progress(0, true);

  const DURATION = data.duration;
  let last = -1;
  window.seek = (t) => {
    t = Math.max(0, Math.min(DURATION, t));
    tl.seek(t, false);
    for (const d of drivers) d(t);
    last = t;
  };
  window.STAGE = { W, H, DURATION, EP };
  window.seek(parseFloat(params.get('t') || '0'));
  window.ready = true;

  if (!RENDER) {
    const stage = document.getElementById('stage');
    const fit = () => {
      const s = Math.min(innerWidth / W, innerHeight / H);
      stage.style.transform = `translate(${(innerWidth - W * s) / 2}px, ${(innerHeight - H * s) / 2}px) scale(${s})`;
    };
    fit();
    addEventListener('resize', fit);
    if (!params.has('t')) {
      const audio = new Audio(`/${EP}.m4a`);
      const hint = document.getElementById('playhint');
      hint.classList.add('show');
      const toggle = () => {
        if (audio.paused) { audio.play(); hint.classList.remove('show'); } else { audio.pause(); hint.classList.add('show'); }
      };
      hint.onclick = toggle;
      stage.onclick = toggle;
      addEventListener('keydown', (e) => {
        if (e.code === 'Space') toggle();
        if (e.code === 'ArrowRight') audio.currentTime += 5;
        if (e.code === 'ArrowLeft') audio.currentTime -= 5;
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
