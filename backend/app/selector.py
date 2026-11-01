"""Margin-based selection: SVM decision function, softmax choice, ask-first gate."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .features import Features
from .profile import Profile


@dataclass
class Selection:
    chosen: int
    margins: list[float]
    normalised_margins: list[float]
    probs: list[float]
    ask_first: bool
    reason: str


def softmax(xs: list[float], beta: float) -> list[float]:
    m = max(xs)
    exps = [math.exp(beta * (x - m)) for x in xs]
    z = sum(exps)
    return [e / z for e in exps]


BAND_SCALE = 0.5  # band half-width = BAND_SCALE * rho, in units of normalised margin


def ask_first_gate(profile: Profile, top_gap: float, top_agreement: float) -> tuple[bool, str]:
    """Directed exploration as a margin test.

    `top_gap` is the separation between the best and second-best draft along the
    hyperplane normal, (m1 - m2) / ||w||: how confidently this profile separates
    its pick from the runner-up. The agent asks one clarifying question when
    (a) the info-bonus dial is on, (b) the pool disagrees on the answer, and
    (c) that separation is inside the uncertainty band, whose width is set by rho.
    """
    if profile.rho <= 0.0:
        return False, "info bonus off"
    if top_agreement >= 1.0:
        return False, "pool agrees"
    band = BAND_SCALE * profile.rho
    if top_gap >= band:
        return False, f"top two drafts separated by {top_gap:.2f} >= band {band:.2f}"
    return True, f"top two drafts separated by only {top_gap:.2f} < band {band:.2f}, and the pool disagrees"


def select(profile: Profile, pool: list[Features], rng: random.Random | None = None) -> Selection:
    rng = rng or random.Random(0)
    vecs = [f.vector() for f in pool]
    margins = [profile.margin(v) for v in vecs]
    nmargins = [profile.normalised_margin(v) for v in vecs]
    probs = softmax(margins, profile.inverse_temperature())
    # sample by softmax (seeded for reproducibility from the log)
    r = rng.random()
    acc = 0.0
    chosen = len(probs) - 1
    for i, p in enumerate(probs):
        acc += p
        if r <= acc:
            chosen = i
            break
    order = sorted(range(len(margins)), key=lambda i: -margins[i])
    top = order[0]
    top_gap = nmargins[top] - (nmargins[order[1]] if len(order) > 1 else 0.0)
    ask, reason = ask_first_gate(profile, top_gap, pool[top].values["agreement"])
    return Selection(chosen=chosen, margins=margins, normalised_margins=nmargins, probs=probs, ask_first=ask, reason=reason)
