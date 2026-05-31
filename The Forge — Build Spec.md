# The Forge — Build Spec v0.1
*A spec compiler for product teams. You drop in a rough idea; an AI engine
refines it through chat, scores it, and won't let it reach a developer until
the spec is actually buildable.*

Working name: **The Forge**. Status: scoping → build. Host: **Railway**.

---

## 1. The product

Most feature requests reach engineers half-baked: vague scope, no acceptance
criteria, hidden dependencies. Devs either guess or bounce it back — both waste
days. The Forge sits between the requester and the developer and **forces the
idea to be complete before it's handed over.**

Two scores make it work:

- **Priority score** — is this worth doing? (impact × reach ÷ effort)
- **Readiness score** — is the spec good enough to build? (ambiguity, missing
  acceptance criteria, undefined edge cases)

A request **cannot be marked "Ready for dev" until readiness clears a
threshold** (default 80%). The refine-chat exists to raise that score. That
gate is the product.

### Who it's for

- **MVP (now):** Adi (requester) + Faktor (developer). One team, one project.
- **Later:** any product team / company — multi-tenant, multiple projects,
  multiple requesters and devs. This is the standalone-SaaS path.

---

## 2. Core flow

```
Rough idea  →  Refine chat  →  Scored + dev-prompt written  →  Board
                  ↑                                              │
                  └──────── Faktor pushes back ──────────────────┘
                          (comments / questions kick it back)
```

1. Requester drops a one-line idea.
2. Engine interrogates only the gaps (error states, which surface, what it
   touches) — each answer raises readiness.
3. At threshold, engine writes the **dev prompt**: problem, scope, acceptance
   criteria, files likely touched, risks/dependencies, explicit out-of-scope.
4. Card lands on the board with both scores.
5. Developer reviews, comments, pushes back. Pushback → card returns to
   Refining and pings the requester.
6. Resolved → **Ready** → developer builds.

---

## 3. The board

Columns: `Refining → Ready → In review → Building → Done`

Each card shows: title, priority score, readiness score, the dev prompt, and a
comment thread. Developer can:

- Comment / ask a question (threaded).
- Push back → card reverts to Refining, notifies requester.
- Move status manually (until the round-trip in §6 automates it).

---

## 4. The engine

Powered by the Anthropic API (Claude). Four jobs:

| Job | What it does |
|---|---|
| **Refine via chat** | Asks the smallest set of gap-closing questions. Stops when readiness clears the bar — no endless interrogation. |
| **Score (priority)** | Impact, reach, effort → single 0–100. Used to rank the backlog. |
| **Score (readiness)** | Penalises ambiguity, missing acceptance criteria, undefined edges. Gates the handoff. |
| **Write dev prompt** | Consistent template: Problem · Scope · Acceptance criteria · Likely files/areas · Risks & dependencies · Out of scope. |
| **Flag risk/deps** | Names what the change touches and what could break or block it. |

**Readiness rubric (starting weights — tune later):**

- Problem clearly stated — 20%
- Scope bounded (in *and* out) — 20%
- Acceptance criteria testable — 25%
- Edge/error cases named — 20%
- Dependencies/risks surfaced — 15%

Each refine answer recomputes the score live so the requester *sees* the bar
rising.

---

## 5. Handoff ladder (start shallow, climb later)

The output is **always a markdown spec** — the only question is how it's
delivered. Build rung 1; leave a seam so 2–3 are config, not a rewrite.

1. **On-board / copy-paste** *(MVP)* — dev reads the prompt on the board.
2. **GitHub issue** — "Mark Ready" opens an issue in the dev's repo with the
   spec as the body.
3. **Committed spec file** — engine PRs the `.md` into a `dev-requests/` folder
   in the repo, so the dev's AI tools (Claude Code / Cursor) ingest it as
   context. *This is the "connect to his code" version.*
4. **Round-trip status** — a PR referencing the request auto-moves the card
   Building → Done.

---

## 6. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Host | **Railway** | Single service; volume for the DB. |
| Backend | FastAPI (Python) | Matches Adi's existing stack. |
| DB | **sqlite** for MVP (two users) → **Postgres** when multi-tenant | Postgres add-on only when concurrent teams demand it. |
| Frontend | React + Vite | Reuse the Odds Primer design tokens if desired. |
| Engine | Anthropic API (Claude / Haiku for cost) | Refine-chat + scoring + prompt-writing. |
| Auth | Shared link / simple login (MVP) → magic-link + org accounts (SaaS) | Two known users now; don't over-build. |
| Integrations | GitHub API (rung 2–4) | Optional, behind a feature flag. |

---

## 7. Data model (MVP)

- **request** — id, title, raw_idea, status, priority_score, readiness_score,
  dev_prompt, created_by, created_at, updated_at
- **message** — id, request_id, role (user/engine), content, created_at
  *(the refine-chat transcript)*
- **comment** — id, request_id, author, body, is_pushback, created_at
- **user** — id, name, role (requester/developer)

Later (multi-tenant): **org**, **project**, request/comment scoped by project.

---

## 8. MVP cut vs later

**MVP (ship this):**

- Request intake + refine-chat
- Both scores + readiness gate
- Dev-prompt generation
- Board with comments + pushback + manual status
- Rung 1 handoff (on-board)

**Later:**

- GitHub issue/PR integration (rungs 2–4)
- Multi-tenant orgs/projects (the SaaS turn)
- Dependency graph across requests
- Analytics: cycle time, pushback rate, what actually ships

---

## 9. Open questions

1. **Readiness threshold** — 80% to start? Should the developer be able to
   accept below-threshold in a pinch?
2. **Who can lower a score** — can Faktor's pushback dock the readiness score
   directly, or only re-open the chat?
3. **Auth for MVP** — shared link good enough, or one login each?
4. **Branding** — reuse Odds Primer look, or neutral (since it's a separate
   product)?

---

*v0.1 — scoped 2026-05-31. Ship rung 1, keep the integration seam clean.*

---

## Scaffold decisions (locked 2026-05-31)

Defaults chosen while scaffolding — all reversible via config:

- **Threshold:** 80, enforced server-side (409 if you try to move to Ready below it).
- **Auth:** none yet for MVP; `SHARED_PASSWORD` env seam left in config for a simple shared login later.
- **Branding:** neutral dark theme for now (not Odds Primer).
- **Engine fallback:** runs heuristically with no API key so the app works end-to-end before a key is wired in.
