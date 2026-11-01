from fastapi.testclient import TestClient

from app import config, db
from app.main import app

client = TestClient(app)


def setup_module(_):
    if config.DB_PATH.exists():
        config.DB_PATH.unlink()
    db.init()


def _profiles():
    return [
        {"id": "sprint", "k": 0.9, "lam": 0.15, "beta": 0.85, "rho": 0.0},
        {"id": "coach", "k": 0.15, "lam": 0.85, "beta": 0.5, "rho": 0.7},
    ]


def test_health_mock():
    r = client.get("/health").json()
    assert r["ok"] and r["mock_mode"] is True


def test_ask_then_feedback_round_trip():
    r = client.post("/ask", json={"prompt": "Solve 3x + 7 = 22 for x", "profiles": _profiles()})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["pool"]) == 4
    assert all(d["features"]["math_ok"] == 1.0 for d in body["pool"])
    sprint, coach = body["results"]
    assert sprint["chosen"] != coach["chosen"] or sprint["margins"] != coach["margins"]
    assert len(sprint["probs"]) == 4

    fb = client.post("/feedback", json={"prompt_id": body["prompt_id"], "profile_id": "coach",
                                        "draft_idx": coach["chosen"], "accepted": False})
    assert fb.status_code == 200, fb.text
    assert fb.json()["profile"]["n_feedback"] == 1
    assert client.get("/profile/coach").json()["n_events"] == 1


def test_feedback_unknown_draft_404():
    assert client.post("/feedback", json={"prompt_id": 9999, "profile_id": "coach", "draft_idx": 0, "accepted": True}).status_code == 404


def test_reset_profile():
    r = client.post("/profile/coach/reset").json()
    assert r["profile"]["n_feedback"] == 0


def test_ambiguous_prompt_makes_coach_ask_first():
    r = client.post("/ask", json={"prompt": "Why does ice float?", "profiles": _profiles()}).json()
    sprint, coach = r["results"]
    assert sprint["ask_first"] is False
    assert coach["ask_first"] is True and coach["clarifying_question"]
    assert coach["agreement"]["share"] == 0.5
