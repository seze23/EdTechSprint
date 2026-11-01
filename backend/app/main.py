"""FastAPI surface for the two-agent study tool."""
from __future__ import annotations

import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, db
from .drafts import generate_pool
from .features import FEATURE_NAMES, extract_pool
from .learner import fit_eta, hinge_update, support_vectors
from .mathcheck import check as math_check
from .profile import Profile
from .selector import select

@asynccontextmanager
async def _lifespan(_: FastAPI):
    db.init()
    yield


app = FastAPI(title="Decision-Profile Agents", version="0.1.0", lifespan=_lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ProfileIn(BaseModel):
    id: str
    name: str | None = None
    k: float = Field(0.5, ge=0, le=1)
    lam: float = Field(0.5, ge=0, le=1)
    beta: float = Field(0.5, ge=0, le=1)
    rho: float = Field(0.0, ge=0, le=1)


class AskIn(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    profiles: list[ProfileIn]
    n: int | None = Field(None, ge=2, le=6)


class FeedbackIn(BaseModel):
    prompt_id: int
    profile_id: str
    draft_idx: int
    accepted: bool


def _apply_dials(p: Profile, pin: ProfileIn) -> Profile:
    p.k, p.lam, p.beta, p.rho = pin.k, pin.lam, pin.beta, pin.rho
    if pin.name:
        p.name = pin.name
    return p


@app.get("/health")
def health():
    return {"ok": True, "mock_mode": config.MOCK_MODE, "model": config.DRAFT_MODEL, "n_drafts": config.N_DRAFTS}


@app.get("/meta")
def meta():
    return {
        "features": FEATURE_NAMES,
        "pricing": {"model": "flat", "stripe_link": config.STRIPE_PAYMENT_LINK,
                     "terms": "One flat price. Cancel in one click. No steps behind a paywall."},
    }


@app.post("/ask")
def ask(body: AskIn):
    drafts, source = generate_pool(body.prompt, body.n)
    prelim = extract_pool(drafts)
    math_scores = math_check(body.prompt, [f.final_answer for f in prelim])
    pool = extract_pool(drafts, math_scores)
    prompt_id = db.log_prompt(body.prompt, source)
    db.log_drafts(prompt_id, drafts, [f.final_answer for f in pool], [f.vector() for f in pool])

    results = []
    for pin in body.profiles:
        p = _apply_dials(db.load_profile(pin.id), pin)
        db.save_profile(p)
        sel = select(p, pool, rng=random.Random(prompt_id * 1000 + hash(p.id) % 1000))
        db.log_selection(prompt_id, p, sel.chosen, sel.margins, sel.probs, sel.ask_first)
        chosen = pool[sel.chosen]
        results.append({
            "profile": p.to_dict(),
            "chosen": sel.chosen,
            "answer": drafts[sel.chosen],
            "final_answer": chosen.final_answer,
            "agreement": {"share": chosen.values["agreement"], "n": len(pool)},
            "margins": sel.margins,
            "normalised_margins": sel.normalised_margins,
            "probs": sel.probs,
            "ask_first": sel.ask_first,
            "ask_reason": sel.reason,
            "clarifying_question": _clarifying_question(pool, drafts) if sel.ask_first else None,
            "contributions": p.contributions(chosen.vector()),
        })
    return {
        "prompt_id": prompt_id,
        "source": source,
        "features": FEATURE_NAMES,
        "pool": [{"idx": i, "text": d, "final_answer": f.final_answer, "features": f.values}
                 for i, (d, f) in enumerate(zip(drafts, pool))],
        "results": results,
    }


def _clarifying_question(pool, drafts) -> str:
    finals = sorted({f.final_answer for f in pool if f.final_answer})
    if len(finals) > 1:
        return f"The drafts disagree ({' vs '.join(finals[:3])}). Which interpretation of the prompt do you mean?"
    return "Before I answer: do you want the result, or the method?"


@app.post("/feedback")
def feedback(body: FeedbackIn):
    f = db.draft_features(body.prompt_id, body.draft_idx)
    if f is None:
        raise HTTPException(404, "unknown prompt/draft")
    p = db.load_profile(body.profile_id)
    step = hinge_update(p, f, body.accepted)
    db.log_feedback(body.prompt_id, body.profile_id, body.draft_idx, body.accepted, f)
    events = db.feedback_events(body.profile_id)
    ep, en = fit_eta(p, events)
    eta_changed = (ep, en) != (p.eta_pos, p.eta_neg)
    p.eta_pos, p.eta_neg = ep, en
    db.save_profile(p)
    return {
        "profile": p.to_dict(),
        "step": step,
        "eta_refit": eta_changed,
        "n_events": len(events),
        "support_vectors": support_vectors(p, events),
    }


@app.get("/profile/{pid}")
def get_profile(pid: str):
    p = db.load_profile(pid)
    events = db.feedback_events(pid)
    return {"profile": p.to_dict(), "n_events": len(events), "support_vectors": support_vectors(p, events)}


@app.post("/profile/{pid}/reset")
def reset_profile(pid: str):
    return {"profile": db.reset_profile(pid).to_dict()}
