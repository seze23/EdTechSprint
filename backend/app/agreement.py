"""Agreement between drafts' final answers.

Numeric answers agree when they are numerically equal. Prose answers agree when
their content-token sets overlap enough (containment coefficient), which keeps
"less dense than liquid water" and "its open hydrogen-bonded lattice makes it
less dense than water" in one cluster while keeping genuinely different claims
apart. Deterministic, no model call, so it stays auditable.
"""
from __future__ import annotations

import re

from .mathcheck import answer_value

_STOP = set("""
a an the and or but of to in on at for from by with as is are was were be been being it its this that these those
than then there their they them which who whom whose what when where why how into onto about because since so such
very can could would should will shall may might must do does did done has have had having not no nor also just
""".split())
_PAREN_RE = re.compile(r"\([^)]*\)")
_TOKEN_RE = re.compile(r"[a-z]+")
CONTAINMENT_THRESHOLD = 0.6


def _stem(t: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(t) > 4 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def content_tokens(answer: str) -> frozenset[str]:
    text = _PAREN_RE.sub(" ", answer.lower())
    return frozenset(_stem(t) for t in _TOKEN_RE.findall(text) if t not in _STOP and len(t) > 1)


def same_answer(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    va, vb = answer_value(a), answer_value(b)
    if va is not None and vb is not None:
        return abs(va - vb) < 1e-6
    if va is not None or vb is not None:
        return False
    ta, tb = content_tokens(a), content_tokens(b)
    if not ta or not tb:
        return False
    if min(len(ta), len(tb)) <= 2:
        return ta == tb
    return len(ta & tb) / min(len(ta), len(tb)) >= CONTAINMENT_THRESHOLD


def agreement_shares(finals: list[str]) -> list[float]:
    """Fraction of the pool in each draft's answer cluster (union-find over same_answer)."""
    n = len(finals)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if same_answer(finals[i], finals[j]):
                parent[find(i)] = find(j)
    roots = [find(i) for i in range(n)]
    return [(roots.count(r) / n) if finals[i] else 0.0 for i, r in enumerate(roots)]
