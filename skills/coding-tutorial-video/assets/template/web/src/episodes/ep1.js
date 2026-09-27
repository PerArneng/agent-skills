// Example episode (pairs with the example script.py). Replace with your own.
// Pattern: every visual change is placed ON the spoken word with word(beatId, 'word'),
// one live accent at a time, holds are real stillness, labels sit on the part they name.
import { tl, B, word, seam, show, hide, C } from '../lib.js';
import { FlowMap, CodePanel, Terminal, card, segTitle, retrieval } from '../ui.js';
import SRC from '../data/source.json';

export default function ep1() {
  // ---------------------------------------------------------------- hook: the problem, in the viewer's world
  const map = new FlowMap({
    x: 960, y: 560,
    nodes: [
      { id: 'you', x: -420, y: 0, shape: 'icon', icon: 'user-round', label: 'you' },
      { id: 'script', x: 0, y: 0, shape: 'box', label: 'script' },
      { id: 'out', x: 420, y: 0, shape: 'icon', icon: 'square-terminal', label: 'terminal' },
    ],
    edges: [{ id: 'run', from: 'you', to: 'script', bend: 0 }, { id: 'print', from: 'script', to: 'out', bend: 0 }],
  });
  map.hideNow(map.all());
  map.showLabels(0, false, undefined, 0.01);
  map.fade(word('hook', 'task'), 'you', 1);
  map.showLabels(word('hook', 'task'), true, 'you');
  map.fade(word('hook', 'computer'), ['run', 'script', 'print', 'out'], 1, 0.8);
  map.showLabels(word('hook', 'computer'), true, ['script', 'out']);
  map.state(word('hook', 'computer'), 'script', 'live');
  map.travel(word('hook', 'computer') + 0.4, word('hook', 'you', 1) + 0.3, ['run', 'print']);

  // ---------------------------------------------------------------- 1 · run it
  const s1 = seam('e1s1').t;
  segTitle('1', 'Run it', s1);
  map.state(s1, 'script', 'idle');
  map.moveTo(s1, { x: 205, y: 262, scale: 0.36 }, 1.2);   // the map docks as a persistent mini-map
  map.showLabels(s1, false);

  const code = new CodePanel(SRC.code['hello.py'], { name: 'hello.py', x: 1100, y: 560, width: 1100,
    lights: { 3: ['sys.argv[1]'], 4: ['print(f"Hello, {name}!")'] } });
  code.show(B('code1').start, 1.0);
  code.focus(word('code1', 'prints'), 4);
  code.light(word('code1', 'greeting'), 4, 'print(f"Hello, {name}!")');
  code.focus(word('code1', 'name'), 3);
  code.light(word('code1', 'name'), 3, 'sys.argv[1]');

  // real captured output, replayed on cue
  code.moveTo(B('run1').start, { x: 560, y: 620, scale: 0.6 });
  const term = new Terminal({ x: 1400, y: 620, width: 900, rows: 5 });
  term.show(B('run1').start + 0.3);
  const t = term.cmd(word('run1', 'python'), 'python hello.py Ada');
  term.out(t + 0.3, SRC.captures['hello.txt'].split('\n').filter(Boolean), { cls: { 0: 'hi' } });
  map.travel(word('run1', 'watch'), word('run1', 'terminal') + 0.4, ['run', 'print']);

  // retrieval: labels hidden, silence, then feedback that morphs the likely wrong answer into the right one
  retrieval('q1', 'different name  →  ?');
  const wrong = card('the whole script changes', { x: 1100, y: 330, cls: 'small muted' });
  show(wrong, B('a1').start, { y: 0 });
  hide(wrong, word('a1', 'only'));
  code.focus(word('a1', 'only'), 3);
  code.light(word('a1', 'name'), 3, 'sys.argv[1]');
  code.focus(word('a1', 'same'), 1, 4);
}
