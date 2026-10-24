# TrialBridge — Frontend Demo

A polished, fully functional React + TypeScript demo for clinical trial matching
and enrollment navigation. It runs entirely on **local fictional mock JSON** — no
backend, no network calls, no LLM.

> All patients and trials are fictional. Not for clinical use.

## Run it

```bash
cd client
npm install
npm run dev      # http://localhost:5173
```

Then click **Load Demo Patient** (or paste/upload fictional `.txt` notes) and work
through the three-step dashboard: intake → review facts → match & refine.

## Scripts

| Command             | What it does                              |
| ------------------- | ----------------------------------------- |
| `npm run dev`       | Start the Vite dev server                 |
| `npm run build`     | Typecheck (`tsc`) + production build      |
| `npm run typecheck` | TypeScript typecheck only                 |
| `npm run lint`      | ESLint                                    |
| `npm run test`      | Run the Vitest suite once                 |
| `npm run test:watch`| Run Vitest in watch mode                  |

## What's inside

- **Step 1 — Intake & facts**: paste/upload fictional notes, deterministic local
  parser extracts supported facts, everything else stays Unknown. Review/correct
  facts before matching.
- **Step 2 — Ranked trial cards**: four fictional studies (DEMO-A…D) with
  supported/unknown/potential-conflict counts and a preliminary screening note.
- **Step 3 — Next Best Question engine**: `src/lib/questionEngine.ts` prioritizes
  the single most useful unresolved question via
  `priority = affectedAssessments / (1 + estimatedEffort)`, with a plain-English
  "Why are we asking this?" explanation.
- **Step 4 — Dynamic updates**: answering recalculates dependent assessments and
  shows a Before vs After diff; answers are revisable.
- **Step 5 — Travel preferences**: reorders cards by labeled mock distance without
  changing any clinical assessment.
- **Step 6 — Eligibility evidence**: expandable accordion with the verbatim mock
  criterion text, patient fact used, and source label.

## Architecture

- `src/types/domain.ts` — all domain interfaces.
- `src/data/` — mock trials + demo patient notes.
- `src/lib/` — pure, unit-tested logic: `noteParser`, `assessor`, `ranking`,
  `questionEngine`, `assessmentDiff`.
- `src/state/` — `useReducer` + context store (immutable updates).
- `src/components/` — UI, built with Tailwind CSS.
- `src/api/adapter.ts` — the single seam for a future backend (currently a local
  mock implementation; documents the future `/api/trials` and `/api/extract-facts`
  contracts).

## Backend integration

The demo never assumes endpoints exist. When a backend is ready, implement
`HttpTrialBridgeApi implements TrialBridgeApi` in `src/api/adapter.ts` and swap the
exported `api`. The Vite dev server already proxies `/api` to the Django backend.
