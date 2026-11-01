from app.features import extract_final_answer, extract_pool
from app.drafts import MOCK_POOLS


def test_final_answer_extraction_normalises():
    assert extract_final_answer("blah\nFINAL ANSWER: x = 5") == "5"
    assert extract_final_answer("FINAL ANSWER: 5") == "5"
    assert extract_final_answer("no marker, ends with 3x = 15") == "15"
    assert extract_final_answer("nothing here") == ""


def test_agreement_is_pool_share():
    pool = extract_pool(["FINAL ANSWER: 5", "FINAL ANSWER: 5", "FINAL ANSWER: 4", "FINAL ANSWER: 5"])
    assert [f.values["agreement"] for f in pool] == [0.75, 0.75, 0.25, 0.75]


def test_mock_pool_features_are_heterogeneous():
    pool = extract_pool(MOCK_POOLS["default"])
    v = [f.values for f in pool]
    assert v[0]["answer_first"] == 1.0 and v[0]["n_steps"] == 0.0
    assert v[1]["n_steps"] > 0 and v[1]["self_check"] == 1.0
    assert v[2]["understanding"] == 1.0 and v[2]["questions"] > 0
    assert v[3]["hedges"] > v[0]["hedges"]
    assert all(f.values["agreement"] == 1.0 for f in pool)
