"""Narration building blocks. A beat is one sentence-sized idea: the voice says it
while one visual change happens, then the picture holds still (the encoding window).
`ask` beats are retrieval questions, followed by a silent window with an amber timer."""

from dataclasses import dataclass, field


@dataclass
class Beat:
    id: str
    say: str
    hold: float = 0.7        # stillness after the sentence, seconds
    ask: bool = False        # retrieval question: slower voice + silent window
    silence: float = 0.0     # length of the silent window after an ask


@dataclass
class Scene:
    """A segment of an episode (60–120 s). Scenes are separated by a settled seam
    with a small title of the next idea."""
    id: str
    title: str
    beats: list[Beat] = field(default_factory=list)


def b(id: str, say: str, hold: float = 0.7) -> Beat:
    return Beat(id, say, hold)


def ask(id: str, say: str, silence: float = 6.0) -> Beat:
    return Beat(id, say, hold=0.4, ask=True, silence=silence)
