# Decision-Profile Agents

Two agents answer the same homework prompt from the same pool of drafts. They differ
only in a small decision profile: discounting (k), loss aversion (λ), choice
determinism (β) and information seeking (ρ). The selector is a linear SVM margin;
feedback is a hinge-loss update with asymmetric learning rates fit from the
student's own log. The spec is in `docs/spec.md`, the algorithm in `docs/algorithm.md`.

## Layout

```
backend/   FastAPI + SQLite. Draft pool from claude-haiku-5-5, or canned drafts in mock mode.
frontend/  Vite + React + TypeScript + Tailwind (Lovable's stack). Reference UI.
docs/      spec.md, algorithm.md, LOVABLE_PROMPT.md
```

## Run

```bash
# backend
conda create -n edtech python=3.11 && conda activate edtech
pip install -r backend/requirements.txt
cp .env.example .env            # leave ANTHROPIC_API_KEY empty for mock mode
cd backend && uvicorn app.main:app --reload      # http://localhost:8000

# frontend (second terminal)
cd frontend && npm install && npm run dev        # http://localhost:5173

# tests
cd backend && pytest -q
```

Set `ANTHROPIC_API_KEY` in `.env` to draw real drafts. The default model is
`claude-haiku-5-5`; it rejects non-default sampling parameters, so draft
diversity comes from per-draft style instructions rather than temperature.

## Supabase

The log store is SQLite until `DATABASE_URL` is set. For Supabase: in the project
dashboard click **Connect**, choose **Transaction pooler** (port 6543), copy the URI,
replace `[YOUR-PASSWORD]` with the database password, and put it in `.env`:

```
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require
```

Tables are created on first start. `backend/supabase/schema.sql` is the same schema
for reference. Run the test suite against it with `TEST_DATABASE_URL=... pytest -q`.

## Public URL without hosting (demo week)

```bash
./scripts/tunnel.sh
```

Starts the backend and a Cloudflare quick tunnel, then prints an https URL. Paste it
into Lovable as `VITE_API_URL`. The URL changes each run, so re-set it after a restart.
Keep the terminal open during the demo.

## Lovable

Start a new Lovable project, paste `docs/LOVABLE_PROMPT.md`, and connect this
repo under Lovable's GitHub settings. Set `VITE_API_URL` to wherever the backend runs.

## What is logged

Every prompt, draft, feature vector, selection (with the profile snapshot that made
it), and accept/reject lands in SQLite. Any pick is reproducible from the log.
