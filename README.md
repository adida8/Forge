# The Forge

A spec compiler for product teams. Drop in a rough idea; the engine refines it
through chat, scores it, and won't let it reach a developer until the spec is
actually buildable. See `The Forge — Build Spec.md` for the full design.

This is the **MVP scaffold** (rung 1 handoff: on-board copy-paste).

## Layout

```
backend/    FastAPI + SQLite + the Anthropic engine
frontend/   React + Vite board UI
```

## Run locally

**1. Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY (optional — see below)
uvicorn app.main:app --reload
```

Backend runs on http://localhost:8000. Health check: `/api/health`.

**2. Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to the backend.

## The engine, with or without a key

The engine runs the Anthropic API (Haiku by default, for cost). **If no
`ANTHROPIC_API_KEY` is set, a heuristic fallback runs instead** — every refine
answer nudges readiness up and a stub dev prompt is produced once the bar is
cleared. This means the whole app works end-to-end for testing before you wire
in a key. The board shows an `engine: live | fallback` pill so you always know
which is active.

## How it works

1. **New request** → engine asks its first gap-closing question.
2. **Refine chat** → each answer recomputes readiness + priority live.
3. **Readiness gate** → a card cannot move to **Ready** until readiness ≥
   `READINESS_THRESHOLD` (default 80). The API enforces this with a 409.
4. **Dev prompt** → written automatically once the bar clears, using a fixed
   template (Problem · Scope · Acceptance criteria · Likely files · Risks &
   dependencies · Out of scope).
5. **Board** → `Refining → Ready → In review → Building → Done`. The developer
   comments, or pushes back — pushback reverts the card to Refining.

## Config (`backend/.env`)

| Var | Default | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Blank = fallback engine. |
| `FORGE_MODEL` | `claude-haiku-4-5-20251001` | Engine model. |
| `READINESS_THRESHOLD` | `80` | The gate. |
| `DATABASE_URL` | `sqlite:///./forge.db` | Point at a volume on Railway, e.g. `sqlite:////data/forge.db`. |
| `CORS_ORIGINS` | `http://localhost:5173` | Frontend origin(s). |

## Deploy (Railway)

`railway.json` builds the frontend and starts the backend as one service. The
backend serves `frontend/dist` if it exists, so a single service covers both.
Add a volume mounted at `/data` and set `DATABASE_URL=sqlite:////data/forge.db`
so the DB survives redeploys. Set `ANTHROPIC_API_KEY` in the service variables.

## What's stubbed for later

GitHub issue/PR handoff (rungs 2–4), multi-tenant orgs/projects, and auth are
intentionally left out. The data model and engine seams are in place so these
are additive, not rewrites.
