# Agent Guide

Use `ty-apm-cli` only as a safe evidence collection layer.

Rules:

- Always parse the JSON envelope from stdout.
- Never expect tables, prompts, or Markdown reports.
- Use `catalog list/search/filter/show` before calling APIs.
- Execute only by `catalog_id`; there is no raw path command.
- Treat `ok=false` envelopes and non-zero exit codes as structured evidence of failure.
- Use `snapshot collect --profile application-context` for a bounded factual portrait of one application.
- Prefer `snapshot collect --profile ... --plan-only` before live snapshot execution.
- Read `snapshot/coverage.json` before analysis so "not collected" is not mistaken for "not present".
- Treat `artifacts/` as sensitive live evidence.
- Use raw call artifacts as evidence; do not expect normalized domain models.
- Treat missing required params as coverage gaps, not as facts about the monitored system.
- Do not ask the CLI for diagnosis, root cause, scoring, recommendations, write actions, host/probe changes, SSH, or server mode.
- Do not attempt write, guarded, or unknown catalog entries.
