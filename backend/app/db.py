"""SQLite log: every prompt, draft, feature vector, selection, and feedback event.

The log is the audit trail and the training set. Profiles are persisted so a
student's learned hyperplane survives a restart.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

from . import config
from .learner import FeedbackEvent
from .profile import Profile, make_default

SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS drafts (
  prompt_id INTEGER NOT NULL,
  idx INTEGER NOT NULL,
  text TEXT NOT NULL,
  final_answer TEXT,
  features TEXT NOT NULL,
  PRIMARY KEY (prompt_id, idx)
);
CREATE TABLE IF NOT EXISTS selections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt_id INTEGER NOT NULL,
  profile_id TEXT NOT NULL,
  chosen INTEGER NOT NULL,
  margins TEXT NOT NULL,
  probs TEXT NOT NULL,
  ask_first INTEGER NOT NULL,
  profile_snapshot TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt_id INTEGER NOT NULL,
  profile_id TEXT NOT NULL,
  draft_idx INTEGER NOT NULL,
  accepted INTEGER NOT NULL,
  features TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,
  data TEXT NOT NULL
);
"""


def init() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.executescript(SCHEMA)


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def log_prompt(text: str, source: str) -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO prompts(text, source) VALUES (?, ?)", (text, source))
        return int(cur.lastrowid)


def log_drafts(prompt_id: int, drafts: list[str], finals: list[str], feats: list[list[float]]) -> None:
    with conn() as c:
        c.executemany(
            "INSERT INTO drafts(prompt_id, idx, text, final_answer, features) VALUES (?,?,?,?,?)",
            [(prompt_id, i, d, f, json.dumps(v)) for i, (d, f, v) in enumerate(zip(drafts, finals, feats))],
        )


def log_selection(prompt_id: int, profile: Profile, chosen: int, margins, probs, ask_first: bool) -> None:
    with conn() as c:
        c.execute(
            "INSERT INTO selections(prompt_id, profile_id, chosen, margins, probs, ask_first, profile_snapshot) VALUES (?,?,?,?,?,?,?)",
            (prompt_id, profile.id, chosen, json.dumps(margins), json.dumps(probs), int(ask_first), json.dumps(profile.to_dict())),
        )


def draft_features(prompt_id: int, idx: int) -> list[float] | None:
    with conn() as c:
        row = c.execute("SELECT features FROM drafts WHERE prompt_id=? AND idx=?", (prompt_id, idx)).fetchone()
        return json.loads(row["features"]) if row else None


def log_feedback(prompt_id: int, profile_id: str, idx: int, accepted: bool, features: list[float]) -> None:
    with conn() as c:
        c.execute(
            "INSERT INTO feedback(prompt_id, profile_id, draft_idx, accepted, features) VALUES (?,?,?,?,?)",
            (prompt_id, profile_id, idx, int(accepted), json.dumps(features)),
        )


def feedback_events(profile_id: str) -> list[FeedbackEvent]:
    with conn() as c:
        rows = c.execute("SELECT features, accepted FROM feedback WHERE profile_id=? ORDER BY id", (profile_id,)).fetchall()
    return [FeedbackEvent(features=json.loads(r["features"]), accepted=bool(r["accepted"])) for r in rows]


def load_profile(pid: str) -> Profile:
    with conn() as c:
        row = c.execute("SELECT data FROM profiles WHERE id=?", (pid,)).fetchone()
    if not row:
        p = make_default(pid)
        save_profile(p)
        return p
    d = json.loads(row["data"])
    return Profile(**{k: d[k] for k in Profile.__dataclass_fields__ if k in d})


def save_profile(p: Profile) -> None:
    from dataclasses import asdict
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO profiles(id, data) VALUES (?, ?)", (p.id, json.dumps(asdict(p))))


def reset_profile(pid: str) -> Profile:
    with conn() as c:
        c.execute("DELETE FROM profiles WHERE id=?", (pid,))
        c.execute("DELETE FROM feedback WHERE profile_id=?", (pid,))
    return load_profile(pid)
