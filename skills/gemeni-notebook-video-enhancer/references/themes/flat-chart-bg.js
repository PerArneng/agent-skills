// Calm 'navy + chart' background (drop-in for src/bg.js): soft brand-colour light pools, thin contour isobars and a
// faint grid. Renders at full resolution × devicePixelRatio because the lines must stay crisp at 4K.
// bgTo(t, pool, accent, warm, energy) still drives it; keep energy low (0.3–0.45) and use bgTo sparingly.
import * as THREE from 'three';
import { bgState, W, H } from './lib.js';

const frag = /* glsl */ `
precision highp float;
uniform float uTime;
uniform vec2 uRes;
uniform vec3 uC1, uC2, uC3;
uniform float uEnergy;
varying vec2 vUv;

float noise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f*f*(3.0-2.0*f);
  float a = fract(sin(dot(i,vec2(127.1,311.7)))*43758.5453);
  float b = fract(sin(dot(i+vec2(1,0),vec2(127.1,311.7)))*43758.5453);
  float c = fract(sin(dot(i+vec2(0,1),vec2(127.1,311.7)))*43758.5453);
  float d = fract(sin(dot(i+vec2(1,1),vec2(127.1,311.7)))*43758.5453);
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  mat2 m = mat2(1.6,1.2,-1.2,1.6);
  for(int i=0;i<5;i++){ v += a*noise(p); p = m*p; a *= 0.5; }
  return v;
}
void main(){
  vec2 uv = vUv;
  vec2 p = (uv - 0.5) * vec2(uRes.x/uRes.y, 1.0) * 2.0;
  float t = uTime * (0.035 + 0.05*uEnergy);
  vec2 q = vec2(fbm(p*0.8 + vec2(0.0, t)), fbm(p*0.8 + vec2(5.2, -t*1.2)));
  float n = fbm(p*0.9 + 2.2*q + vec2(1.7, 9.2) + t*0.6);

  // navy base (site --ff-navy-500) with soft coloured light pools
  vec3 base = vec3(0.0, 0.066, 0.13);
  vec3 col = base;
  col = mix(col, uC1, smoothstep(0.35, 1.0, n) * 0.42);
  col = mix(col, uC2, smoothstep(0.6, 1.05, q.x * 1.35) * 0.22);
  col = mix(col, uC3, smoothstep(0.62, 1.05, q.y * n * 2.0) * 0.16);

  // chart isobars: thin contour lines of the flow field
  float h = n * 14.0;
  float w = fwidth(h);
  float iso = smoothstep(w*1.5, 0.0, min(fract(h), 1.0 - fract(h)));
  col += iso * 0.045 * mix(vec3(0.42,0.95,0.98), uC3*2.0, 0.25);

  // aeronautical chart grid
  vec2 g = uv * uRes / (uRes.y / 12.0);
  vec2 gw = fwidth(g);
  vec2 gl = smoothstep(gw * 1.2, vec2(0.0), min(fract(g), 1.0 - fract(g)));
  col += max(gl.x, gl.y) * 0.022;

  // vertical legibility falloff
  float v = smoothstep(1.3, 0.2, length((uv-vec2(0.5,0.5))*vec2(1.0,1.2)));
  col *= 0.55 + 0.5*v;
  gl_FragColor = vec4(col, 1.0);
}`;

export function createBg(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, alpha: false });
  // full stage resolution × device pixel ratio so the thin chart lines stay crisp in the 4K render
  const PR = window.devicePixelRatio || 1;
  renderer.setPixelRatio(1);
  renderer.setSize(W * PR, H * PR, false);
  const scene = new THREE.Scene();
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const uniforms = {
    uTime: { value: 0 }, uRes: { value: new THREE.Vector2(W * PR, H * PR) },
    uC1: { value: new THREE.Vector3() }, uC2: { value: new THREE.Vector3() }, uC3: { value: new THREE.Vector3() },
    uEnergy: { value: 0.5 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms, fragmentShader: frag,
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position,1.0); }',
  });
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat));
  return (t) => {
    const s = bgState;
    uniforms.uTime.value = t + 40.0;
    uniforms.uC1.value.set(s.c1r, s.c1g, s.c1b);
    uniforms.uC2.value.set(s.c2r, s.c2g, s.c2b);
    uniforms.uC3.value.set(s.c3r, s.c3g, s.c3b);
    uniforms.uEnergy.value = s.energy;
    renderer.render(scene, cam);
  };
}
