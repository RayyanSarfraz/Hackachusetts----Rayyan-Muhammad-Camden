---
name: postgres-best-practices
description: "Postgres best practices maintained by Supabase, for Postgres running anywhere. Load this skill BEFORE writing or changing anything that lives in a Postgres database: creating or altering tables and columns (including choosing column types), schema design, migrations and declarative schema files, RLS policies and the tests that verify them, indexes, triggers, database functions, queues and scheduled jobs (pg_cron, pgmq), vector/semantic search (pgvector), and restoring dumps (pg_restore) or importing data. Also load it when diagnosing slow queries, high CPU, timeouts, EXPLAIN plans, connection exhaustion, locking, bloat, or rows visible to the wrong user or tenant. This is not just a performance guide — schema, migration, security, and SQL authoring tasks need these rules too, even for a one-column change or a single query."
license: MIT
metadata:
  author: supabase
  version: "1.1.1"
  organization: Supabase
  date: January 2026
  abstract: Comprehensive Postgres performance optimization guide for developers using Supabase and Postgres. Contains performance rules across 8 categories, prioritized by impact from critical (query performance, connection management) to incremental (advanced features). Each rule includes detailed explanations, incorrect vs. correct SQL examples, query plan analysis, and specific performance metrics to guide automated optimization and code generation.
---

# PostgreSQL Design and Operations

## Using this skill

Read the [shared guide](../../AGENTS.md). Apply this domain guidance with any capable assistant, editor, CLI, SDK, API, or supported UI. Follow installed versions and project conventions; examples do not require adopting their exact stack. Load related guidance only when its subject is part of the task.


## Workflow

- Inspect the PostgreSQL version, schema, workload, extensions, and hosting constraints before proposing changes.
- Choose column types, constraints, keys, and indexes from data semantics and access patterns. Do not assume a particular hosted platform.
- Review migration locking, table rewrites, compatibility, backfill batches, rollback, and backups according to the change's impact.
- Parameterize values and grant least privilege. Where tenant isolation or RLS is used, test both permitted and denied access using realistic roles.
- Diagnose performance with query plans and representative data; EXPLAIN ANALYZE executes the statement, so use an appropriate safe environment.
- Consider connection pooling, transaction length, contention, and index maintenance before adding capacity.
- Validate schema and query changes in an appropriate test database and report measured results.

Provider-specific features, including Supabase authentication helpers, apply only when that provider is actually used. Detailed rule references from the original package are not bundled here; consult version-matched PostgreSQL documentation when needed.

## Related guidance

- [django-backend](../../agents/django-backend/AGENTS.md)
- [pandas](../../agents/pandas/AGENTS.md)
- [django](../django/SKILL.md)
- [django-testing](../django-testing/SKILL.md)
