from app.agreement import agreement_shares, same_answer

ICE = [
    "ice floats because its open hydrogen-bonded crystal structure makes it less dense than liquid water",
    "ice floats because it is less dense than liquid water (about 917 vs. 1000 kg/m³), since water expands into an open hydrogen-bonded crystal structure when it freezes",
    "ice floats because its hydrogen-bonded crystal structure holds molecules farther apart, making ice less dense (about 0.92 g/cm³) than liquid water (about 1.00 g/cm³)",
    "ice floats because its open, hydrogen-bonded crystal structure makes it less dense than liquid water",
]


def test_numeric_answers_cluster_by_value():
    assert agreement_shares(["x = 5", "5", "5.0", "4"]) == [0.75, 0.75, 0.75, 0.25]


def test_prose_paraphrases_cluster_together():
    assert agreement_shares(ICE) == [1.0] * 4


def test_different_claims_stay_apart():
    finals = ["ice is less dense than water", "hydrogen bonding forces an open lattice",
              "ice is less dense than water", "hydrogen bonding forces an open lattice"]
    assert agreement_shares(finals) == [0.5] * 4


def test_boundaries():
    assert same_answer("", "5") is False                     # empty never agrees
    assert same_answer("5", "five apples") is False          # numeric vs prose
    assert same_answer("paris", "paris") is True
    assert same_answer("paris", "london") is False           # short answers: smaller set must be a subset
    assert same_answer("yes, 0.999... equals 1", "yes, 0.999... is exactly equal to 1") is True
    assert same_answer("yes", "no") is False
    assert agreement_shares(["", ""]) == [0.0, 0.0]
