# Data Analysis and Transformation

Use for applications and analyses using pandas dataframes.

## Shared conventions

Read the [shared guide](../../AGENTS.md) for scope, portability, and coordination. This role is optional task guidance, not an instruction to launch another agent. Use the tools available in the current environment and the target project's actual configuration.

## Workflow

- Inspect data sources, schema, dtypes, units, missing values, and dataset size before transforming data.
- Specify parsing and join assumptions, including time zones, key uniqueness, null semantics, and expected row counts.
- Prefer clear vectorized operations where suitable; avoid chained assignment and accidental mutation of shared data.
- Validate merge cardinality and aggregation behavior. Protect identifiers and precision during conversions.
- For large inputs, estimate memory, select columns/dtypes deliberately, and consider chunking or an existing scalable engine.
- Make outputs reproducible and preserve source provenance. Check representative values, boundary cases, and summary invariants.
- Use the application's environment and tests; upstream library build and contribution rules apply only when working in that library.

## Related guidance

- [Model and Dataset Workflows](../hugging-face/AGENTS.md)
- [LLM Workflow Integration](../langchain/AGENTS.md)
- [Django Backend](../django-backend/AGENTS.md)
- [postgreSQL](../../skills/postgreSQL/SKILL.md)
