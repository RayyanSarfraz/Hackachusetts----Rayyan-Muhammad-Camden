# TrialBridge PR #2 — integration fixes

## What changed

- Geographic distance is calculated from the patient coordinates before practical-fit ranking; rankings do not mutate input trials.
- Fixture getters return independent deep copies so requests cannot contaminate each other.
- Synthetic eligibility fixture corrected: invented demo requirements are labeled as such; eGFR exclusion inversion was removed. **Do not use demo criteria for real medical decisions.**
- Clarification question IDs are stable per fact, and a question can affect all criteria requiring that fact.
- Answering a question automatically updates only **explicit boolean rules** (`expected_value`); ambiguous or complex medical criteria remain `unknown` until the clinical assessment module evaluates them.
- `/answer/` and `/preferences/` are stateless: they require the same patient and trials the client is working with. They never silently switch to the demo patient.
- `/answer/` returns a sanitized patient summary, changed trials, and a new comparison. It does not return the raw patient profile.
- Added regression tests for ranking, fixture isolation, and explicit-rule reassessment.

## API usage

`POST /api/integration/compare/` accepts `{ "patient": {...}, "trials": [...] }` and returns comparison results.

`POST /api/integration/answer/` accepts `{ "patient": {...}, "trials": [...], "question_id": "q_...", "answer": "no" }`.
It returns `updated_profile` (sanitized summary), `trials` (updated assessment list), `comparison`, `affected_criteria`, and `requires_reassessment`. The client must retain the patient profile locally, apply the answered fact locally, and send the updated profile with returned trials on the next request. An `unknown` answer must stay unknown.

`POST /api/integration/preferences/` accepts `{ "patient": {...}, "trials": [...], "preferences": { "max_travel_miles": 150 } }`. It returns comparison fields plus `trials`.

`GET /api/integration/demo/` returns fictional demo data only.

## Security and clinical limitations

**Hackathon demo only.** Endpoints remain public and accept clinical information. Do not upload real patient notes or real personal health information. Production requires authentication/authorization, encrypted storage and transport, privacy review, audit controls, consent, and a validated clinical assessment service. `criteria` may contain clinical evidence, so API results are not generally safe for public display. The synthetic examples cite real NCT IDs but contain invented criteria and should not be presented as authoritative clinical trial requirements.

## Verification

`cd api && python -m unittest apps.integration.tests` — 42 tests passed in the editing environment.

Full Django REST endpoint tests could not be run in the editing environment because Django/DRF were not installed. Run `python manage.py test apps.integration` in your configured project environment before merging.
