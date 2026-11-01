"""A decision profile is a hyperplane.

Four dials (k, lam, beta, rho) set a prior weight vector over the draft
features. Feedback moves a learned correction `w_learned` and a bias `b`.
The agent's utility for a draft is its signed distance to that hyperplane:

    margin_i = (w_prior(k, lam) + w_learned) . f_i + b

Drafts on the positive side are ones this student is predicted to accept.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict

from .features import FEATURE_NAMES, NOW_FEATURES, LATER_FEATURES

MATH_WEIGHT = 1.5  # everyone wants the math to be right; not a dial


@dataclass
class Profile:
    id: str
    name: str
    k: float = 0.5      # 0 = learn it (later), 1 = answer now
    lam: float = 0.5    # 0 = just tell me, 1 = flag uncertainty
    beta: float = 0.5   # 0 = surprise me (soft), 1 = consistent (sharp)
    rho: float = 0.0    # 0 = assume, 1 = ask first
    eta_pos: float = 0.15
    eta_neg: float = 0.15
    w_learned: list[float] = field(default_factory=lambda: [0.0] * len(FEATURE_NAMES))
    b: float = 0.0
    n_feedback: int = 0

    # ---- dial -> prior hyperplane -------------------------------------
    def w_prior(self) -> list[float]:
        w = []
        for name in FEATURE_NAMES:
            if name in NOW_FEATURES:
                w.append(2.0 * self.k)                      # discount: pay-off-now features
            elif name in LATER_FEATURES:
                w.append(2.0 * (1.0 - self.k))              # pay-off-later features
            elif name == "agreement":
                w.append(0.5 + 2.5 * self.lam)              # loss aversion rewards consensus
            elif name == "hedges":
                w.append(2.0 * (self.lam - 0.5))            # low lam punishes hedging, high lam rewards it
            elif name == "questions":
                w.append(1.5 * (self.rho - 0.5))            # info bonus rewards asking
            elif name == "math_ok":
                w.append(MATH_WEIGHT)
            else:
                w.append(0.0)
        return w

    def w(self) -> list[float]:
        return [p + l for p, l in zip(self.w_prior(), self.w_learned)]

    def inverse_temperature(self) -> float:
        # beta in [0,1] -> [0.5, 12] on a log scale; keeps softmax well behaved
        return 0.5 * math.exp(self.beta * math.log(24.0))

    def margin(self, f: list[float]) -> float:
        return sum(wi * fi for wi, fi in zip(self.w(), f)) + self.b

    def normalised_margin(self, f: list[float]) -> float:
        norm = math.sqrt(sum(wi * wi for wi in self.w())) or 1.0
        return self.margin(f) / norm

    def contributions(self, f: list[float]) -> dict[str, float]:
        return {n: wi * fi for n, wi, fi in zip(FEATURE_NAMES, self.w(), f)}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["w_prior"] = dict(zip(FEATURE_NAMES, self.w_prior()))
        d["w_total"] = dict(zip(FEATURE_NAMES, self.w()))
        d["w_learned_named"] = dict(zip(FEATURE_NAMES, self.w_learned))
        d["inverse_temperature"] = self.inverse_temperature()
        return d


DEFAULT_PROFILES = {
    "sprint": dict(name="Sprint", k=0.9, lam=0.15, beta=0.85, rho=0.0),
    "coach": dict(name="Coach", k=0.15, lam=0.85, beta=0.5, rho=0.7),
}


def make_default(pid: str) -> Profile:
    spec = DEFAULT_PROFILES.get(pid, dict(name=pid.title(), k=0.5, lam=0.5, beta=0.5, rho=0.3))
    return Profile(id=pid, **spec)
