"""Numeric sanity check with sympy where the prompt is a solvable equation.

Returns 1.0 (extracted answer matches sympy), 0.0 (contradicts), 0.5 (unknown).
Deliberately conservative: a wrong 'unknown' is cheap, a wrong 'match' is not.
"""
from __future__ import annotations

import re

from sympy import Eq, solve, symbols, sympify
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TRANS = standard_transformations + (implicit_multiplication_application,)
_EQ_RE = re.compile(r"([0-9a-zA-Z+\-*/^().\s]+)=([0-9a-zA-Z+\-*/^().\s]+)")
_WORD_RE = re.compile(r"[A-Za-z]{2,}")   # prose words; single letters are variables


def _parse(s: str):
    return parse_expr(s.replace("^", "**"), transformations=_TRANS)


def reference_solutions(prompt: str) -> list[float] | None:
    """Try to recover a numeric solution set from a prompt like 'Solve 3x + 7 = 22 for x'."""
    # Replace prose words with a delimiter so the equation span is just the math.
    cleaned = _WORD_RE.sub("|", prompt)
    m = None
    for chunk in cleaned.split("|"):
        m = _EQ_RE.search(chunk)
        if m:
            break
    if not m:
        return None
    try:
        lhs, rhs = _parse(m.group(1)), _parse(m.group(2))
    except Exception:
        return None
    free = (lhs.free_symbols | rhs.free_symbols)
    if len(free) != 1:
        return None
    (x,) = free
    try:
        sols = solve(Eq(lhs, rhs), x)
    except Exception:
        return None
    out = []
    for s in sols:
        try:
            out.append(float(s))
        except Exception:
            return None
    return out or None


def answer_value(final_answer: str) -> float | None:
    if not final_answer:
        return None
    s = final_answer.strip()
    s = re.sub(r"^[a-zA-Z]\s*=\s*", "", s)
    s = re.sub(r"[^0-9a-zA-Z+\-*/^().]", "", s)
    if not s:
        return None
    try:
        return float(sympify(s.replace("^", "**")))
    except Exception:
        return None


def check(prompt: str, final_answers: list[str]) -> list[float]:
    ref = reference_solutions(prompt)
    if ref is None:
        return [0.5] * len(final_answers)
    scores = []
    for a in final_answers:
        v = answer_value(a)
        if v is None:
            scores.append(0.5)
        else:
            scores.append(1.0 if any(abs(v - r) < 1e-6 for r in ref) else 0.0)
    return scores
