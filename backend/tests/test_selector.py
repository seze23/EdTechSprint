import math
import random

from app.drafts import MOCK_POOLS
from app.features import extract_pool
from app.profile import Profile, make_default
from app.selector import ask_first_gate, select, softmax


def test_softmax_sums_to_one_and_sharpens_with_beta():
    xs = [1.0, 0.5, 0.0]
    soft = softmax(xs, 0.5)
    sharp = softmax(xs, 12.0)
    assert math.isclose(sum(soft), 1.0) and math.isclose(sum(sharp), 1.0)
    assert sharp[0] > soft[0] > 1 / 3


def test_ask_first_gate_boundaries():
    p = Profile(id="t", name="t", rho=0.0)
    assert ask_first_gate(p, 0.0, 0.5) == (False, "info bonus off")
    p.rho = 0.5                                               # band = 0.25
    assert ask_first_gate(p, 0.0, 1.0)[0] is False            # pool agrees -> never ask
    assert ask_first_gate(p, 0.25, 0.5)[0] is False           # exactly at band edge clears it
    assert ask_first_gate(p, 0.24, 0.5)[0] is True            # inside band + disagreement -> ask
    assert ask_first_gate(p, 0.26, 0.5)[0] is False
    p.rho = 1.0                                               # band = 0.5
    assert ask_first_gate(p, 0.49, 0.5)[0] is True


def test_sprint_and_coach_diverge_on_same_pool():
    pool = extract_pool(MOCK_POOLS["default"])
    sprint, coach = make_default("sprint"), make_default("coach")
    s_top = max(range(4), key=lambda i: sprint.margin(pool[i].vector()))
    c_top = max(range(4), key=lambda i: coach.margin(pool[i].vector()))
    assert s_top == 0, "Sprint should prefer the answer-first draft"
    assert c_top in (1, 2), "Coach should prefer a worked or teaching draft"
    assert s_top != c_top


def test_select_is_reproducible_from_seed():
    pool = extract_pool(MOCK_POOLS["default"])
    p = make_default("coach")
    a = select(p, pool, rng=random.Random(7))
    b = select(p, pool, rng=random.Random(7))
    assert a.chosen == b.chosen and a.margins == b.margins


def test_contributions_sum_to_margin():
    pool = extract_pool(MOCK_POOLS["default"])
    p = make_default("sprint")
    f = pool[0].vector()
    assert math.isclose(sum(p.contributions(f).values()) + p.b, p.margin(f))
