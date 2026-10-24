---
inclusion: always
---

# Project Structure

Part of the [unified team agent memory](team-agent-memory.md). Records file
organization and naming conventions. Update when the layout changes.

## Top level

```
.
├── api/            # Django REST backend
├── client/         # React 19 + TypeScript + Vite + Tailwind frontend
├── data/           # datasets (e.g. data/trials/data.csv — ClinicalTrials.gov export)
├── ml/             # MedGemma fine-tuning (Colab notebook + model_a scripts)
├── .kiro/          # agents, skills, and steering (team memory)
├── compose.yaml    # dev stack: db + api + client
├── .env / .env.example   # root compose env (gitignored .env)
├── audit_guidance.py
├── skills-lock.json
└── README.md
```

## Backend (`api/`)

```
api/
├── manage.py
├── requirements.txt
├── Dockerfile / entrypoint.sh / .dockerignore
├── .env / .env.example
├── config/                 # project configuration
│   ├── settings/           # base.py, development.py, production.py
│   ├── urls.py             # root URLConf, mounts modules under /api/
│   ├── asgi.py / wsgi.py
└── apps/                   # feature modules (modular monolith)
    ├── users/              # email auth + JWT; User + PatientProfile models
    │   ├── models.py  serializers.py  views.py  urls.py  admin.py
    │   └── migrations/
    ├── engine/             # intake, extraction, retrieval, matching pipeline
    │   ├── models.py            # Trial (Postgres source of truth)
    │   ├── serializers.py  views.py  urls.py  admin.py
    │   ├── services/            # patient_processor, medical_extractor,
    │   │                        #   model_client, retriever, ai_matcher,
    │   │                        #   ranker, pipeline
    │   ├── management/commands/ # ingest_trials
    │   └── tests/               # test_intake_api, test_patient_processor,
    │                            #   test_medical_extractor
    └── integration/        # trial comparison/ranking/clarification (Camden)
        ├── contracts.py (dataclasses)  ranking.py  clarification.py
        ├── orchestrator.py  fixtures.py  frontend_demo.py
        ├── views.py  serializers.py  urls.py  tests.py
        └── (no DB models — in-memory, dataclass-based)
```

## Frontend (`client/src/`)

```
src/
├── App.tsx  main.tsx  index.css
├── api/          # adapter.ts (TrialBridgeApi seam) + __tests__
├── components/   # intake, results, trial cards, ui/ (TypeScript)
├── lib/          # noteParser, assessor, ranking, questionEngine (pure, tested)
├── state/        # store.ts + AppContext.tsx
├── data/         # demoPatient.ts, trials.ts (fictional mock data)
├── types/        # domain.ts
└── __tests__/ test/   # Vitest integration + setup
```

## Conventions

- **Modular monolith.** Each feature is a self-contained module under `apps/`
  with its own `models`, `views`, `serializers`, `urls`, `admin`, and
  `migrations`. `apps/` is on `sys.path`, so import modules as `apps.<module>`.
- **URL mounting.** Each module exposes its own URLConf; `config/urls.py` mounts
  them under the `/api/` prefix (e.g. `/api/users/`).
- **Settings split.** Shared config in `config/settings/base.py`; environment
  overrides in `development.py` / `production.py`. `BASE_DIR` is the `api/` folder.
- **New feature module checklist:** create `apps/<name>/`, add it to `LOCAL_APPS`
  in `base.py`, give it a `urls.py`, and mount it in `config/urls.py`.
- **UUID primary keys** on every model (see decisions.md). `engine.Trial` keeps
  `nct_id` as the public business key alongside its UUID PK.
- **Ownership:** `apps/integration/` is Camden's; coordinate before editing. See
  [integration.md](integration.md).
