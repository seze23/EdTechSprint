"""Draft generation: one pool of N candidates that every profile scores.

Uses claude-haiku-5-5 (Haiku-class, as the spec asks). Haiku 5.5 rejects
non-default sampling parameters, so draft diversity comes from per-draft
style instructions rather than temperature. In MOCK mode (no API key) a
canned, deliberately heterogeneous pool is returned so the demo runs free.
"""
from __future__ import annotations

from . import config

SYSTEM = (
    "You are answering a student's homework prompt. Follow the STYLE instruction exactly. "
    "Always end with a single line of the form 'FINAL ANSWER: <answer>' (for non-numeric prompts, "
    "a one-sentence answer). Do not use markdown headers."
)

STYLES = [
    "STYLE: Give the final answer in the first sentence. Then at most two short sentences. No hedging.",
    "STYLE: Numbered worked steps (3-6), each one line. Verify the result by substituting back ('Check: ...'). Final answer last.",
    "STYLE: Teach it. Ask the student to try the first step themselves ('Your turn: ...'), then show the solution with a check for understanding. If the prompt is ambiguous, ask one clarifying question first.",
    "STYLE: Explain the idea in plain words, flag anything you are unsure about, and give the answer with any caveats.",
    "STYLE: Shortest correct response possible.",
]

MOCK_POOLS = {
    "default": [
        "x = 5. Subtract 7 from both sides and divide by 3.\nFINAL ANSWER: x = 5",
        "1. Start with 3x + 7 = 22.\n2. Subtract 7: 3x = 15.\n3. Divide by 3: x = 5.\nCheck: 3(5) + 7 = 22. ✓\nFINAL ANSWER: 5",
        "Your turn: what happens if you subtract 7 from both sides? Try it before reading on.\n\nYou should get 3x = 15. Now divide both sides by 3 to isolate x. Do you see why dividing undoes the multiplication? That gives x = 5. Can you check it by plugging 5 back in?\nFINAL ANSWER: x = 5",
        "The idea is to undo operations in reverse order. We might first remove the +7, then the ×3. I think that gives 3x = 15, so x is probably 5, though it is worth double-checking the arithmetic.\nFINAL ANSWER: 5",
    ],
    # A pool that disagrees, so the ask-first gate has something to fire on offline.
    "ambiguous": [
        "Because ice is less dense than liquid water.\nFINAL ANSWER: ice is less dense than water",
        "1. Water molecules form hydrogen bonds.\n2. On freezing they lock into a hexagonal lattice.\n3. That lattice holds molecules farther apart than in the liquid.\nCheck: the lattice spacing explains the ~9% volume increase.\nFINAL ANSWER: hydrogen bonding forces an open lattice",
        "Your turn: what happens to the spacing between molecules when water freezes? Try to predict it before reading on.\n\nThe hexagonal lattice spreads molecules out, so the solid is lighter per volume than the liquid. Do you see why that is unusual for a solid?\nFINAL ANSWER: ice is less dense than water",
        "It depends what you mean by why. Chemically, I think it is hydrogen bonding; physically it is density. Possibly both answers are acceptable depending on the course.\nFINAL ANSWER: hydrogen bonding forces an open lattice",
    ],
}


def _mock_pool(prompt: str, n: int) -> list[str]:
    pool = MOCK_POOLS["default"] if any(ch.isdigit() for ch in prompt) else MOCK_POOLS["ambiguous"]
    return (pool * ((n // len(pool)) + 1))[:n]


def generate_pool(prompt: str, n: int | None = None) -> tuple[list[str], str]:
    """Returns (drafts, source) where source is 'mock' or the model id."""
    n = n or config.N_DRAFTS
    if config.MOCK_MODE:
        return _mock_pool(prompt, n), "mock"

    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    drafts: list[str] = []
    for i in range(n):
        style = STYLES[i % len(STYLES)]
        resp = client.messages.create(
            model=config.DRAFT_MODEL,
            max_tokens=1500,
            system=SYSTEM,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": f"{style}\n\nPROMPT: {prompt}"}],
        )
        if resp.stop_reason == "refusal":
            drafts.append("I can't help with that prompt.\nFINAL ANSWER: declined")
            continue
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        drafts.append(text or "FINAL ANSWER: (empty)")
    return drafts, config.DRAFT_MODEL
