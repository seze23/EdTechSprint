"""Log store: every prompt, draft, feature vector, selection, and feedback event.

Two backends behind one interface:
  * SQLite (default, local dev and tests): DB_PATH
  * Postgres / Supabase: DATABASE_URL=postgresql://...

SQL is written in the dialect both accept (RETURNING, ON CONFLICT ... DO UPDATE)
with '?' placeholders that are rewritten to '%s' for Postgres.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict

from . import config
from .learner import FeedbackEvent
from .profile import Profile, make_default

_TABLES = """
CREATE TABLE IF NOT EXISTS prompts (
  id {pk},
  text TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at {ts}
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
  id {pk},
  prompt_id INTEGER NOT NULL,
  profile_id TEXT NOT NULL,
  chosen INTEGER NOT NULL,
  margins TEXT NOT NULL,
  probs TEXT NOT NULL,
  ask_first INTEGER NOT NULL,
  seed INTEGER NOT NULL DEFAULT 0,
  profile_snapshot TEXT NOT NULL,
  created_at {ts}
);
CREATE TABLE IF NOT EXISTS feedback (
  id {pk},
  prompt_id INTEGER NOT NULL,
  profile_id TEXT NOT NULL,
  draft_idx INTEGER NOT NULL,
  accepted INTEGER NOT NULL,
  features TEXT NOT NULL,
  created_at {ts}
);
CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,
  data TEXT NOT NULL
);
"""

SQLITE_SCHEMA = _TABLES.format(pk="INTEGER PRIMARY KEY AUTOINCREMENT", ts="TEXT DEFAULT CURRENT_TIMESTAMP")
POSTGRES_SCHEMA = _TABLES.format(pk="SERIAL PRIMARY KEY", ts="TIMESTAMPTZ DEFAULT now()")


# ---- backend selection ------------------------------------------------------

def is_postgres() -> bool:
    return config.DATABASE_URL.startswith(("postgres://", "postgresql://"))


def backend_name() -> str:
    return "postgres" if is_postgres() else "sqlite"


def _q(sql: str) -> str:
    return sql.replace("?", "%s") if is_postgres() else sql


@contextmanager
def conn():
    if is_postgres():
        import psycopg
        from psycopg.rows import dict_row
        # prepare_threshold=None: Supabase's transaction-mode pooler (port 6543)
        # does not support server-side prepared statements.
        c = psycopg.connect(config.DATABASE_URL, row_factory=dict_row, prepare_threshold=None)
    else:
        c = sqlite3.connect(config.DB_PATH)
        c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init() -> None:
    if is_postgres():
        with conn() as c:
            for stmt in POSTGRES_SCHEMA.split(";"):
                if stmt.strip():
                    c.execute(stmt)
    else:
        config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with conn() as c:
            c.executescript(SQLITE_SCHEMA)


def _one(c, sql: str, params=()):
    cur = c.execute(_q(sql), params)
    return cur.fetchone()


def _all(c, sql: str, params=()):
    cur = c.execute(_q(sql), params)
    return cur.fetchall()


# ---- writes -----------------------------------------------------------------

def log_prompt(text: str, source: str) -> int:
    with conn() as c:
        row = _one(c, "INSERT INTO prompts(text, source) VALUES (?, ?) RETURNING id", (text, source))
        return int(row["id"])


def log_drafts(prompt_id: int, drafts: list[str], finals: list[str], feats: list[list[float]]) -> None:
    with conn() as c:
        c.cursor().executemany(
            _q("INSERT INTO drafts(prompt_id, idx, text, final_answer, features) VALUES (?,?,?,?,?)"),
            [(prompt_id, i, d, f, json.dumps(v)) for i, (d, f, v) in enumerate(zip(drafts, finals, feats))],
        )


def log_selection(prompt_id: int, profile: Profile, chosen: int, margins, probs, ask_first: bool, seed: int) -> None:
    with conn() as c:
        c.execute(
            _q("INSERT INTO selections(prompt_id, profile_id, chosen, margins, probs, ask_first, seed, profile_snapshot) "
               "VALUES (?,?,?,?,?,?,?,?)"),
            (prompt_id, profile.id, chosen, json.dumps(margins), json.dumps(probs), int(ask_first), seed,
             json.dumps(profile.to_dict())),
        )


def log_feedback(prompt_id: int, profile_id: str, idx: int, accepted: bool, features: list[float]) -> None:
    with conn() as c:
        c.execute(
            _q("INSERT INTO feedback(prompt_id, profile_id, draft_idx, accepted, features) VALUES (?,?,?,?,?)"),
            (prompt_id, profile_id, idx, int(accepted), json.dumps(features)),
        )


def save_profile(p: Profile) -> None:
    with conn() as c:
        c.execute(
            _q("INSERT INTO profiles(id, data) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data = excluded.data"),
            (p.id, json.dumps(asdict(p))),
        )


def reset_profile(pid: str) -> Profile:
    with conn() as c:
        c.execute(_q("DELETE FROM profiles WHERE id=?"), (pid,))
        c.execute(_q("DELETE FROM feedback WHERE profile_id=?"), (pid,))
    return load_profile(pid)


# ---- reads ------------------------------------------------------------------

def draft_features(prompt_id: int, idx: int) -> list[float] | None:
    with conn() as c:
        row = _one(c, "SELECT features FROM drafts WHERE prompt_id=? AND idx=?", (prompt_id, idx))
    return json.loads(row["features"]) if row else None


def feedback_events(profile_id: str) -> list[FeedbackEvent]:
    with conn() as c:
        rows = _all(c, "SELECT features, accepted FROM feedback WHERE profile_id=? ORDER BY id", (profile_id,))
    return [FeedbackEvent(features=json.loads(r["features"]), accepted=bool(r["accepted"])) for r in rows]


def load_profile(pid: str) -> Profile:
    with conn() as c:
        row = _one(c, "SELECT data FROM profiles WHERE id=?", (pid,))
    if not row:
        p = make_default(pid)
        save_profile(p)
        return p
    d = json.loads(row["data"])
    return Profile(**{k: d[k] for k in Profile.__dataclass_fields__ if k in d})
