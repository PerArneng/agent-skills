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
  vec2 p = (uv - 0.5) * vec2(uRes.x/uRes.y, 1.0) * 2.2;
  float t = uTime * (0.06 + 0.05*uEnergy);
  vec2 q = vec2(fbm(p + vec2(0.0, t)), fbm(p + vec2(5.2, -t*1.3)));
  vec2 r = vec2(fbm(p + 3.5*q + vec2(1.7, 9.2) + t*0.8), fbm(p + 3.5*q + vec2(8.3, 2.8) - t*0.6));
  float n = fbm(p + 3.0*r);

  vec3 base = vec3(0.012, 0.010, 0.045);
  vec3 col = mix(base, uC1, smoothstep(0.15, 0.85, n));
  col = mix(col, uC2, smoothstep(0.35, 1.0, r.x) * 0.85);
  col = mix(col, uC3, smoothstep(0.45, 1.0, q.y*r.y*1.8) * 0.9);
  // iridescent ribbons
  float rib = sin((n*6.0 + r.y*4.0) + uTime*0.25);
  col += 0.07 * uEnergy * vec3(0.5+0.5*sin(rib+0.0), 0.5+0.5*sin(rib+2.1), 0.5+0.5*sin(rib+4.2));
  // darken toward bottom/top for legibility
  float v = smoothstep(1.25, 0.25, length((uv-vec2(0.5,0.45))*vec2(1.0,1.15)));
  col *= 0.35 + 0.75*v;
  col *= 0.8;
  gl_FragColor = vec4(col, 1.0);
}`;

export function createBg(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, alpha: false });
  // BG_RES 0.5 = half resolution (fine for a soft gradient, ~4x cheaper per frame). Use 1 if the shader draws
  // thin lines (grids, contours) that must stay crisp. Multiplied by devicePixelRatio so --scale 2 (4K) keeps detail.
  const BG_RES = 0.5, PR = (window.devicePixelRatio || 1) * BG_RES;
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
