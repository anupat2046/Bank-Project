# Contributing

This repository contains a public-data analytics platform for Thailand's provincial banking markets. Keep changes auditable and support capability, deployment, and data-quality claims with verifiable evidence.

## Before making a change

1. Read the [architecture](docs/architecture.md), [data contract](docs/data-sources.md), and relevant analytical/evaluation guide.
2. Separate source retrieval time, observation period, and publication/revision availability.
3. Keep customer data, credentials, raw operational traces, and personal drafts out of public artifacts.

## Verification

From the repository root, with the populated local database running:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tools.evaluate_chat
.\.venv\Scripts\python.exe -m tools.check_docs
git diff --check
```

For frontend changes, run `npm run typecheck` and `npm run build` in `frontend/`; inspect affected desktop/mobile flows. Passing automated checks does not replace a targeted UI check.

Live LLM evaluations require explicit opt-in, private local configuration, and a bounded request budget. Do not selectively rerun failed model answers and report only successes. Once a held-out set has been inspected for tuning, create a new held-out split for subsequent claims.

## Publishing evidence

- State the verification date/timezone, warehouse scope, implementation/model version, and checks performed.
- Distinguish offline regression, function-level benchmark, HTTP integration smoke, browser checks, and scheduler operations.
- Keep historical raw reports unchanged. Add a new named run rather than overwriting evidence.
- Label design concepts and historical screenshots; do not present sample values as measured output.
- Regenerate competency evidence only after deliberately running the exporter; it updates tracked reports from the current warehouse.
- Inspect staged diffs for secrets and internal paths. Ignoring a file does not remove it from existing Git history.

Use focused commits, update affected guides, and preserve unrelated local changes. No CI badge or automated deployment guarantee should be added without a configured workflow and observed results.
