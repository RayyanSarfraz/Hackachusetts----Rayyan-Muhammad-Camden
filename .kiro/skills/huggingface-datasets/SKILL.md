---
name: huggingface-datasets
description: Use this skill for Hugging Face Dataset Viewer API workflows that fetch subset/split metadata, paginate rows, search text, apply filters, download parquet URLs, and read size or statistics.
---

# Hugging Face Dataset Viewer

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

Use Dataset Viewer API calls for read-only exploration and extraction. Creating or uploading datasets is a separate operation and applies only when requested.

## Core workflow

1. Optionally validate dataset availability with `/is-valid`.
2. Resolve `config` + `split` with `/splits`.
3. Preview with `/first-rows`.
4. Paginate content with `/rows` using `offset` and `length` (max 100).
5. Use `/search` for text matching and `/filter` for row predicates.
6. Retrieve parquet links via `/parquet` and totals/metadata via `/size` and `/statistics`.

## Defaults

- Base URL: `https://datasets-server.huggingface.co`
- Default API method: `GET`
- Query params should be URL-encoded.
- `offset` is 0-based.
- `length` max is usually `100` for row-like endpoints.
- Gated/private datasets require `Authorization: Bearer <HF_TOKEN>`.

## Dataset Viewer

- `Validate dataset`: `/is-valid?dataset=<namespace/repo>`
- `List subsets and splits`: `/splits?dataset=<namespace/repo>`
- `Preview first rows`: `/first-rows?dataset=<namespace/repo>&config=<config>&split=<split>`
- `Paginate rows`: `/rows?dataset=<namespace/repo>&config=<config>&split=<split>&offset=<int>&length=<int>`
- `Search text`: `/search?dataset=<namespace/repo>&config=<config>&split=<split>&query=<text>&offset=<int>&length=<int>`
- `Filter with predicates`: `/filter?dataset=<namespace/repo>&config=<config>&split=<split>&where=<predicate>&orderby=<sort>&offset=<int>&length=<int>`
- `List parquet shards`: `/parquet?dataset=<namespace/repo>`
- `Get size totals`: `/size?dataset=<namespace/repo>`
- `Get column statistics`: `/statistics?dataset=<namespace/repo>&config=<config>&split=<split>`
- `Get Croissant metadata (if available)`: `/croissant?dataset=<namespace/repo>`

Pagination pattern:

```bash
curl "https://datasets-server.huggingface.co/rows?dataset=stanfordnlp/imdb&config=plain_text&split=train&offset=0&length=100"
curl "https://datasets-server.huggingface.co/rows?dataset=stanfordnlp/imdb&config=plain_text&split=train&offset=100&length=100"
```

When pagination is partial, use response fields such as `num_rows_total`, `num_rows_per_page`, and `partial` to drive continuation logic.

Search/filter notes:

- `/search` matches string columns (full-text style behavior is internal to the API).
- `/filter` requires predicate syntax in `where` and optional sort in `orderby`.
- Keep filtering and searches read-only and side-effect free.

For CLI-based parquet URL discovery or SQL, use the `hf-cli` skill with `hf datasets parquet` and `hf datasets sql`.

## Creating and Uploading Datasets

Use one of these flows depending on dependency constraints.

Zero local dependencies (Hub UI):

- Create dataset repo in browser: `https://huggingface.co/new-dataset`
- Upload parquet files in the repo "Files and versions" page.
- Verify shards appear in Dataset Viewer:

```bash
curl -s "https://datasets-server.huggingface.co/parquet?dataset=<namespace>/<repo>"
```

Low dependency CLI flow (`npx @huggingface/hub` / `hfjs`):

- Set auth token:

```bash
export HF_TOKEN=<your_hf_token>
```

- Upload parquet folder to a dataset repo (auto-creates repo if missing):

```bash
npx -y @huggingface/hub upload datasets/<namespace>/<repo> ./local/parquet-folder data
```

- Upload as private repo on creation:

```bash
npx -y @huggingface/hub upload datasets/<namespace>/<repo> ./local/parquet-folder data --private
```

After upload, call `/parquet` to discover `<config>/<split>/<shard>` values for querying with `@~parquet`.

## Optional session-trace datasets

Only handle session traces when explicitly requested. Identify the actual trace format and location from the selected tool and user scope; do not assume an assistant-specific home directory. Inspect for sensitive content before any authorized upload, agree the destination and visibility, and default new trace datasets to private. Dataset exploration does not authorize collecting or uploading local sessions.

## Related guidance

- [hf-cli](../hf-cli/SKILL.md)
- [pandas-best-practices](../pandas-best-practices/SKILL.md)
