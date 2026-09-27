"""THE per-project file: what the tutorial teaches, what it shows, how it sounds.

Replace everything below with your tutorial. The example is a tiny one-episode
lesson about a Python script, just enough to smoke-test the pipeline.
"""

from beats import Scene, ask, b

PROJECT = dict(
    title="Hello, script",
    # the real project the tutorial builds; code panels read these files verbatim
    code_dir="example",
    code_files=["hello.py"],
    # real terminal output captured from running that project (see references/capture.md)
    captures_dir="captures",
    capture_files=["hello.txt"],
    # narration voice (Gemini TTS). One model + one voice for the whole series:
    # switching either mid-series changes how the narrator sounds.
    tts_model="gemini-3.1-flash-tts-preview",
    voice="Sulafat",
    persona="""# AUDIO PROFILE: Maya L.
## "The Patient Code Mentor"

## THE SCENE: A quiet home studio
A small, sound-treated room with a close microphone. Maya sits beside one learner
at a laptop, walking them through the lesson. Focused, friendly, unhurried.

### DIRECTOR'S NOTES
Style: Warm, calm enthusiasm, like a mentor who enjoys this topic. A subtle vocal
smile. Natural pitch movement, never monotone and never salesy. Slight stress on
technical terms and code names.

Pacing: Deliberately relaxed, like explaining to someone who is taking notes.
Short pauses at commas, and a full breath between sentences.

Accent: Neutral, clear General American English.

#### TRANSCRIPT
""",
    # how on-screen names should be spoken (regex → spoken form); captions keep the original
    pronounce=[(r"\bpy\b", "pie"), (r"\bCLI\b", "C.L.I."), (r"\bAPI\b", "A.P.I.")],
)

EPISODE_TITLES = {"ep1": "Part 1 · Hello, script"}

EPISODES = {
    "ep1": [
        Scene("e1s0", "Hook", [
            b("hook", "You have a task you repeat every day. Let's make the computer do it for you."),
        ]),
        Scene("e1s1", "Run it", [
            b("code1", "Here's the whole script. It prints a greeting, with your name in it."),
            b("run1", "Run it with python, and watch the terminal."),
            ask("q1", "Your turn. What would change if you passed a different name?", 5.0),
            b("a1", "Only the name in the greeting. The script itself stays the same."),
        ]),
    ],
}
