"""Online hinge-loss learning with asymmetric learning rates.

This is Pegasos-style SGD on a linear SVM, with the reward-prediction-error
flavour from the spec: an outcome only moves the weights when it was
surprising, i.e. when the chosen draft sat inside the margin or on the wrong
side of it. Accepts move w by eta_pos, rejects by eta_neg. eta is not set by
the student; it is re-fit from their own log (see `fit_eta`).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .features import FEATURE_NAMES
from .profile import Profile

REG = 0.01          # L2 shrink on the learned correction
MARGIN_TARGET = 1.0 # hinge target


@dataclass
class FeedbackEvent:
    features: list[float]
    accepted: bool

    @property
    def y(self) -> int:
        return 1 if self.accepted else -1


def hinge_update(profile: Profile, f: list[float], accepted: bool) -> dict:
    """Mutates profile.w_learned / profile.b in place; returns the step taken."""
    y = 1 if accepted else -1
    eta = profile.eta_pos if accepted else profile.eta_neg
    m = profile.margin(f)
    surprised = y * m < MARGIN_TARGET
    before = list(profile.w_learned)
    if surprised:
        profile.w_learned = [
            (1 - eta * REG) * wl + eta * y * fi for wl, fi in zip(profile.w_learned, f)
        ]
        profile.b += eta * y
    else:
        profile.w_learned = [(1 - eta * REG) * wl for wl in profile.w_learned]
    profile.n_feedback += 1
    delta = dict(zip(FEATURE_NAMES, [a - b for a, b in zip(profile.w_learned, before)]))
    return {"surprised": surprised, "margin_before": m, "y": y, "eta": eta, "delta_w": delta}


def support_vectors(profile: Profile, events: list[FeedbackEvent]) -> list[int]:
    """Indices of logged judgments that currently sit on or inside the margin.

    These are the past accepts/rejects the current hyperplane 'rests on'.
    """
    return [i for i, e in enumerate(events) if e.y * profile.margin(e.features) <= MARGIN_TARGET]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def replay_loglik(base: Profile, events: list[FeedbackEvent], eta_pos: float, eta_neg: float) -> float:
    """Log-likelihood of the observed accept/reject sequence under (eta_pos, eta_neg).

    Runs the model forward from the dial prior with w_learned reset, predicting
    P(accept) = sigmoid(margin) before each update. Same logic as fitting eta
    to a rodent's choice sequence; here the 'choices' are the student's verdicts.
    """
    p = Profile(id=base.id, name=base.name, k=base.k, lam=base.lam, beta=base.beta, rho=base.rho,
                eta_pos=eta_pos, eta_neg=eta_neg)
    ll = 0.0
    for e in events:
        pa = _sigmoid(p.margin(e.features))
        pa = min(max(pa, 1e-6), 1 - 1e-6)
        ll += math.log(pa if e.accepted else 1 - pa)
        hinge_update(p, e.features, e.accepted)
    return ll


ETA_GRID = [0.02, 0.05, 0.1, 0.15, 0.25, 0.4]


def fit_eta(base: Profile, events: list[FeedbackEvent]) -> tuple[float, float]:
    """Grid-search eta_pos, eta_neg by replay likelihood. Needs >= 5 events to move."""
    if len(events) < 5:
        return base.eta_pos, base.eta_neg
    best = (-math.inf, base.eta_pos, base.eta_neg)
    for ep in ETA_GRID:
        for en in ETA_GRID:
            ll = replay_loglik(base, events, ep, en)
            if ll > best[0]:
                best = (ll, ep, en)
    return best[1], best[2]


def refit_from_log(base: Profile, events: list[FeedbackEvent]) -> Profile:
    """Rebuild the learned correction from the full log with the fitted eta."""
    ep, en = fit_eta(base, events)
    p = Profile(id=base.id, name=base.name, k=base.k, lam=base.lam, beta=base.beta, rho=base.rho,
                eta_pos=ep, eta_neg=en)
    for e in events:
        hinge_update(p, e.features, e.accepted)
    return p
