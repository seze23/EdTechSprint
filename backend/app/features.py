"""Deterministic feature extraction over candidate drafts.

Every feature is cheap, reproducible, and in roughly [0, 1] so that the
hyperplane weights are comparable across features. The feature vector is
the only thing the selector sees, which is what makes a choice auditable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .agreement import agreement_shares

FEATURE_NAMES = [
    "answer_first",     # final answer appears in the first 20% of the text
    "brevity",          # 1 - clipped(word_count / 250)
    "n_steps",          # numbered / bulleted step count, clipped at 8, /8
    "self_check",       # draft verifies its own result
    "understanding",    # draft asks the student to try something / checks understanding
    "hedges",           # hedge-word count, clipped at 5, /5
    "questions",        # questions directed at the student, clipped at 3, /3
    "agreement",        # fraction of the pool whose final answer matches this draft's (numeric or fuzzy prose)
    "math_ok",          # sympy check: 1 match, 0 mismatch, 0.5 unknown
]
# Which features "pay off now" vs "pay off later" (the discount axis).
NOW_FEATURES = {"answer_first", "brevity"}
LATER_FEATURES = {"n_steps", "self_check", "understanding"}

_FINAL_RE = re.compile(r"final answer\s*[:=]\s*(.+)", re.IGNORECASE)
_STEP_RE = re.compile(r"^\s*(?:\d+[.)]|step\s*\d+|[-*•])\s+", re.IGNORECASE | re.MULTILINE)
_HEDGES = [
    "might", "may be", "maybe", "possibly", "perhaps", "i think", "not sure",
    "roughly", "approximately", "likely", "probably", "could be", "i believe",
]
_SELF_CHECK = ["check:", "verify", "plug back", "sanity", "double-check", "substitut", "confirm"]
_UNDERSTANDING = ["try this", "your turn", "can you", "do you see", "before reading on", "pause here", "what do you think"]


@dataclass
class Features:
    values: dict[str, float]
    final_answer: str

    def vector(self) -> list[float]:
        return [self.values[n] for n in FEATURE_NAMES]


def extract_final_answer(text: str) -> str:
    m = _FINAL_RE.search(text)
    if m:
        return _normalise_answer(m.group(1))
    # fallback: last line that contains a digit or '='
    for line in reversed([l.strip() for l in text.splitlines() if l.strip()]):
        if any(ch.isdigit() for ch in line) or "=" in line:
            return _normalise_answer(line.split("=")[-1])
    return ""


def _normalise_answer(s: str) -> str:
    s = s.strip().strip("*`.").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("$", "")
    # keep things like "x = 4" and "4" comparable
    if "=" in s:
        s = s.split("=")[-1].strip()
    return s.lower()


def _count_terms(text: str, terms: list[str]) -> int:
    low = text.lower()
    return sum(low.count(t) for t in terms)


def _answer_position(text: str, final: str) -> float:
    if not final:
        return 0.0
    low = text.lower()
    idx = low.find(final)
    if idx < 0:
        m = _FINAL_RE.search(text)
        idx = m.start() if m else -1
    if idx < 0:
        return 0.0
    return 1.0 if idx / max(len(text), 1) <= 0.20 else 0.0


def extract_pool(drafts: list[str], math_scores: list[float] | None = None) -> list[Features]:
    """Extract features for a whole pool so that `agreement` can be computed."""
    finals = [extract_final_answer(d) for d in drafts]
    shares = agreement_shares(finals)
    out: list[Features] = []
    for i, (text, final) in enumerate(zip(drafts, finals)):
        words = len(text.split())
        n_q = len([s for s in re.split(r"(?<=[.?!])\s+", text) if s.strip().endswith("?")])
        values = {
            "answer_first": _answer_position(text, final),
            "brevity": max(0.0, 1.0 - min(words, 250) / 250.0),
            "n_steps": min(len(_STEP_RE.findall(text)), 8) / 8.0,
            "self_check": 1.0 if _count_terms(text, _SELF_CHECK) > 0 else 0.0,
            "understanding": 1.0 if _count_terms(text, _UNDERSTANDING) > 0 else 0.0,
            "hedges": min(_count_terms(text, _HEDGES), 5) / 5.0,
            "questions": min(n_q, 3) / 3.0,
            "agreement": shares[i],
            "math_ok": (math_scores[i] if math_scores else 0.5),
        }
        out.append(Features(values=values, final_answer=final))
    return out
