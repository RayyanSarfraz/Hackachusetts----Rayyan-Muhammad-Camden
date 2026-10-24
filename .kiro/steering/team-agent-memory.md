---
inclusion: always
---

# Unified Team Agent Memory

This is the shared, durable memory for every agent and collaborator in this
repository. It is the index and protocol; the actual knowledge lives in the
companion steering files below. All of them are always included so each session
starts from the same facts, decisions, and conventions instead of rediscovering
them.

This memory supplements, and never overrides, the user's explicit task,
environment permissions, and `.kiro/AGENTS.md`. Those win on conflict.

## Memory files

| File | What it holds |
| --- | --- |
| [product.md](product.md) | Project goals and features — what we're building and why. |
| [tech.md](tech.md) | Technology stack, versions, and common commands. |
| [structure.md](structure.md) | File organization and naming conventions. |
| [architecture.md](architecture.md) | Backend and frontend design. |
| [decisions.md](decisions.md) | Dated log of team decisions and rationale. |
| [progress.md](progress.md) | Current progress, next steps, and open questions. |

## How to use this memory

- Read the relevant files at the start of a task and prefer what they record over
  assumptions. If a recorded fact conflicts with the code, trust the code, then
  update the file.
- When you learn something a future session would otherwise have to rediscover,
  write it into the right file (see the protocol below).
- Do not record secrets, credentials, tokens, or the contents of `api/.env`.
  Reference configuration by key name only.

## Memory protocol

1. **Read first.** Load the relevant memory files before starting work and rely
   on them over guesses.
2. **Record durable facts only.** Capture structural facts, team decisions,
   non-obvious gotchas, naming conventions, and resolved questions. Skip routine
   step-by-step actions.
3. **Put it in the right file.** Goals/features → `product.md`; stack/commands →
   `tech.md`; layout → `structure.md`; design → `architecture.md`; a choice and
   its rationale → `decisions.md`; status and next steps → `progress.md`.
4. **Date entries.** Prefix decisions and progress updates with `YYYY-MM-DD` so
   staleness is visible. Keep `decisions.md` newest-first and refresh the
   "Last updated" line in `progress.md`.
5. **Supersede, don't duplicate.** Edit or mark the old entry rather than
   appending a contradictory one.
6. **Prune.** Move resolved open questions out of `progress.md`. Keep each file
   lean so it stays worth reading.
7. **Protect secrets.** Never store credentials, tokens, or `.env` values.
