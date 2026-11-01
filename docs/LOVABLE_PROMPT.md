# Lovable build prompt

Paste the block below into a new Lovable project. Then connect this GitHub repo
in Lovable's GitHub settings (Lovable links an existing repo to a new project; it
does not import code as a starting point, so the `frontend/` folder here is a
working reference implementation you can point Lovable at or replace).

Run the backend locally or on any host and set `VITE_API_URL` in Lovable's
environment to its URL.

---

Build a single-page study tool called "Two agents, one prompt". Stack: Vite, React,
TypeScript, Tailwind, shadcn/ui. Calm, neutral palette (stone greys, one emerald and
one rose accent for accept/reject). No marketing hero, no gradients.

**Layout, top to bottom**

1. Header: title "Two agents, one prompt." and one paragraph of disclosure: both
   agents read the same drafts and differ only in how they value them; they are
   deliberately different; one is tuned for the problem set due tonight, the other
   for the exam next month. Show a small status line from `GET /health`
   (mock mode vs. model name; red warning if the backend is unreachable).
2. Prompt bar: one text input prefilled with "Solve 3x + 7 = 22 for x" and an
   "Ask both" button. Submitting calls `POST /ask`.
3. Two agent cards side by side (three if the user adds one). Each card has:
   - an editable name (defaults "Sprint" and "Coach"),
   - four range sliders 0–1 with end labels and the live value:
     `k` "Learn it ↔ Answer now", `λ` "Just tell me ↔ Flag uncertainty",
     `β` "Surprise me ↔ Consistent", `ρ` "Assume ↔ Ask first",
   - the chosen answer text (preserve newlines),
   - if `ask_first` is true, an amber callout above the answer with
     `clarifying_question` and the small-print `ask_reason`,
   - a pill "N of M drafts agree" computed from `agreement.share * agreement.n`,
   - a monospace pill with the chosen draft's margin and pick probability,
   - a "why this draft?" toggle revealing a signed horizontal bar chart of
     `contributions` (feature name, bar centred at zero, green positive, red
     negative) and the list of drafts ranked by margin,
   - Accept / Reject buttons that call `POST /feedback`,
   - a "Profile drift" panel: `n_feedback`, `eta_pos`/`eta_neg` with a "(re-fit)"
     tag when `eta_refit` is true, a signed bar chart of `w_learned_named`, and a
     sentence saying whether the last judgment moved the weights
     (`step.surprised`) and how many past judgments are support vectors
     (`support_vectors.length` of `n_events`),
   - a small "reset learning" link calling `POST /profile/{id}/reset`.
4. "+ add a third agent" link (max three).
5. Collapsible "shared draft pool" panel listing every draft with its final answer
   and its feature values as small monospace chips.
6. Footer: "One flat price. Cancel in one click. No steps behind a paywall. Free
   while this is a demo." and a button linking to `VITE_STRIPE_LINK`.

**API contract** (base URL from `VITE_API_URL`, default `http://localhost:8000`)

`POST /ask` body: `{ prompt: string, profiles: [{ id, name, k, lam, beta, rho }] }`
returns
```
{ prompt_id, source, features: string[],
  pool: [{ idx, text, final_answer, features: Record<string, number> }],
  results: [{ profile: { id, name, k, lam, beta, rho, eta_pos, eta_neg, b, n_feedback,
                         w_prior, w_total, w_learned_named, inverse_temperature },
              chosen, answer, final_answer,
              agreement: { share, n },
              margins: number[], normalised_margins: number[], probs: number[],
              ask_first: boolean, ask_reason: string, clarifying_question: string|null,
              contributions: Record<string, number> }] }
```
`POST /feedback` body: `{ prompt_id, profile_id, draft_idx, accepted }` returns
`{ profile, step: { surprised, margin_before, y, eta, delta_w }, eta_refit, n_events, support_vectors: number[] }`.
`GET /profile/{id}`, `POST /profile/{id}/reset`, `GET /health`, `GET /meta`.

Keep all copy flat and literal. No exclamation marks. No "AI-powered".
