import math

from app.features import FEATURE_NAMES
from app.learner import FeedbackEvent, fit_eta, hinge_update, refit_from_log, support_vectors
from app.profile import Profile

N = len(FEATURE_NAMES)


def _unit(i):
    v = [0.0] * N
    v[i] = 1.0
    return v


def test_accept_inside_margin_moves_toward_draft():
    p = Profile(id="t", name="t", k=0.5, lam=0.5, eta_pos=0.2, eta_neg=0.2)
    f = _unit(FEATURE_NAMES.index("hedges"))  # prior weight on hedges at lam=0.5 is 0 -> margin 0 -> surprised
    step = hinge_update(p, f, accepted=True)
    assert step["surprised"] is True
    assert p.w_learned[FEATURE_NAMES.index("hedges")] > 0
    assert p.b > 0


def test_reject_inside_margin_moves_away():
    p = Profile(id="t", name="t", eta_pos=0.2, eta_neg=0.2)
    f = _unit(FEATURE_NAMES.index("hedges"))
    hinge_update(p, f, accepted=False)
    assert p.w_learned[FEATURE_NAMES.index("hedges")] < 0
    assert p.b < 0


def test_no_update_when_draft_clears_margin():
    p = Profile(id="t", name="t", k=1.0)  # answer_first prior weight 2.0 -> margin 2.0 > 1
    f = _unit(FEATURE_NAMES.index("answer_first"))
    step = hinge_update(p, f, accepted=True)
    assert step["surprised"] is False
    assert all(abs(w) < 1e-12 for w in p.w_learned) and p.b == 0.0


def test_asymmetric_learning_rates():
    f = _unit(FEATURE_NAMES.index("hedges"))
    a = Profile(id="a", name="a", eta_pos=0.1, eta_neg=0.4)
    b = Profile(id="b", name="b", eta_pos=0.1, eta_neg=0.4)
    hinge_update(a, f, accepted=True)
    hinge_update(b, f, accepted=False)
    assert math.isclose(abs(b.w_learned[FEATURE_NAMES.index("hedges")]), 4 * abs(a.w_learned[FEATURE_NAMES.index("hedges")]), rel_tol=1e-9)


def test_fit_eta_needs_five_events_then_moves():
    base = Profile(id="t", name="t", eta_pos=0.15, eta_neg=0.15)
    f = _unit(FEATURE_NAMES.index("hedges"))
    few = [FeedbackEvent(f, True)] * 4
    assert fit_eta(base, few) == (0.15, 0.15)
    many = [FeedbackEvent(f, True)] * 8  # consistent accepts -> a large eta_pos explains the data best
    ep, en = fit_eta(base, many)
    assert ep >= 0.25


def test_support_vectors_are_inside_margin_events():
    p = Profile(id="t", name="t", k=1.0)
    far = FeedbackEvent(_unit(FEATURE_NAMES.index("answer_first")), True)   # margin 2 -> not a support vector
    near = FeedbackEvent(_unit(FEATURE_NAMES.index("hedges")), True)        # margin 0 -> support vector
    assert support_vectors(p, [far, near]) == [1]


def test_refit_from_log_is_deterministic():
    base = Profile(id="t", name="t")
    events = [FeedbackEvent(_unit(i % N), i % 3 != 0) for i in range(12)]
    a, b = refit_from_log(base, events), refit_from_log(base, events)
    assert a.w_learned == b.w_learned and a.b == b.b
