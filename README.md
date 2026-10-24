# TrialBridge

Clinical trial matching demo for Hackachusetts. A patient's notes go in, and ranked trial
matches come out, with every eligibility criterion marked met, conflict or unknown, plus
the single most useful follow-up question to ask next.

> **All patient and trial data is fictional. Not for clinical use.** Do not enter real
> patient information: the demo endpoints are public and unauthenticated.

## Run the demo

### Frontend only (fastest, no backend needed)

```bash
cd client
npm install
npm run dev          # http://localhost:5173
```

Click **Load Demo Patient**, review the extracted facts, then work through the ranked
trial cards, the Next Best Question panel and the travel preference filter.

### Full stack (Docker)

```bash
docker compose up --build      # Postgres + Django API (:8000) + Vite client (:5173)
```

To have the frontend call the backend for fact extraction, set `VITE_USE_HTTP_API=true`
for the client (for example in `client/.env.local`). The trial list still comes from the
frontend's built-in data; the backend's `/api/trials/` returns the same four trials.

### Backend without Docker

```bash
cd api
python -m venv .venv
source .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then set DATABASE_URL, e.g. sqlite:///db.sqlite3 for local use
python manage.py migrate
python manage.py runserver
```

## Tests

| Part | Command | Count |
|---|---|---|
| Backend | `cd api && python manage.py test apps` | 77 |
| ML (Model A, no GPU) | `cd ml/model_a && python -m unittest discover -s tests -t .` (needs `pyyaml`) | 30 |
| Frontend | `cd client && npm test && npm run typecheck && npm run lint && npm run build` | 32 |
| Backend-frontend parity | start the API, then `cd client && RUN_PARITY=1 npx vitest run src/api/__tests__/parity.test.ts --environment node` | 2 |

## What's where

| Path | Owner | What it is |
|---|---|---|
| `client/` | Arjun | React + TypeScript demo: intake, fact review, ranked trials, Next Best Question engine. See `client/README.md`. |
| `api/apps/integration/` | Camden | Ranking, clarification questions and comparison endpoints. See `INTEGRATION.md`. |
| `api/apps/engine/` | Rayyan | Patient intake and trial search (`/api/engine/intake/`, `/api/engine/trials/`, login required). |
| `api/apps/users/` | Rayyan | Auth (JWT register/login) and the `PatientProfile` model. |
| `ml/model_a/` | Muhammad | MedGemma 1.5 extraction fine-tune (Colab/GPU). See `ml/model_a/README.md`. |

## API endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health/` | no | Health check |
| GET | `/api/trials/` | no | Demo trials in the frontend's `Trial` shape |
| POST | `/api/extract-facts/` | no | `{ notes }` returns patient facts (unknown facts stay `null`) |
| GET | `/api/integration/demo/` | no | Full synthetic comparison |
| POST | `/api/integration/compare/` | no | `{ patient, trials }` returns ranked results and questions |
| POST | `/api/integration/answer/` | no | Apply a clarification answer |
| POST | `/api/integration/preferences/` | no | Re-rank on travel preferences only |
| POST | `/api/users/auth/register/`, `/api/users/auth/login/` | no | JWT auth |
| POST | `/api/engine/intake/` | yes | Normalize and store a patient profile |
| POST | `/api/engine/trials/` | yes | Trial retrieval (needs a Chroma store) |

## Current limitations

- The model server and trial vector store aren't configured, so `/api/engine/intake/`
  reports `model_available: false` and `/api/engine/trials/` returns no trials. This is
  intentional: the engine reports what's missing instead of inventing results.
- The frontend doesn't call the engine endpoints yet and has no login screen.
- The backend doesn't call the Model A extraction model yet.
- The demo scenarios differ: the frontend uses lung cancer, the integration fixtures use
  diabetes, and the Model A example uses chest pain.
