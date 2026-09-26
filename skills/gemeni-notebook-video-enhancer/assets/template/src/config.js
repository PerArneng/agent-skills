import cfg from '../config.json';
// Single source of truth for stage size / fps / duration (written by scripts/scaffold.sh).
export const W = cfg.width, H = cfg.height, FPS = cfg.fps, DURATION = cfg.duration;
export const CONFIG = cfg;
