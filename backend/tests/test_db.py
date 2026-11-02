"""Store-level round trip. Runs on SQLite by default; set TEST_DATABASE_URL to run on Supabase."""
from app import db
from app.profile import make_default


def test_round_trip_through_store():
    db.init()
    pid = db.log_prompt("2 + 2", "mock")
    assert isinstance(pid, int) and pid > 0
    db.log_drafts(pid, ["FINAL ANSWER: 4", "FINAL ANSWER: 5"], ["4", "5"], [[0.1] * 9, [0.2] * 9])
    assert db.draft_features(pid, 1) == [0.2] * 9
    assert db.draft_features(pid, 7) is None

    p = make_default("coach")
    db.log_selection(pid, p, 0, [1.0, 0.5], [0.6, 0.4], False, 42)
    db.log_feedback(pid, "coach", 0, True, [0.1] * 9)
    assert db.feedback_events("coach")[-1].accepted is True

    p.b = 0.75
    db.save_profile(p)
    db.save_profile(p)                      # upsert, second write must not raise
    assert db.load_profile("coach").b == 0.75
    assert db.reset_profile("coach").b == 0.0


def test_placeholder_rewrite_matches_backend():
    sql = "SELECT ? , ?"
    assert db._q(sql) == ("SELECT %s , %s" if db.is_postgres() else sql)
