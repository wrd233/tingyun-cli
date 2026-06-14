# ty-apm-cli

Agent-first CLI for Tingyun APM official APIs. The first version is built from the provided PDF API manual and is designed for Codex / Claude Code style automation: stable JSON stdout, traceable catalog evidence, strict read-only execution, redacted secrets, and archived run artifacts.

## What Is Included

- Structured catalog generated from `/Users/wangrundong/Downloads/基调听云应用与微服务API说明.pdf`
- 275 catalog entries: 274 PDF endpoint candidates plus the token endpoint
- Read-only raw caller for `safety=read`
- Hard refusal for `guarded`, `write`, and `unknown`
- `api_key + secret_key + timestamp` MD5 token flow
- Token cache, token clear, redaction, and artifact archival
- Typed commands for auth, catalog, business systems, applications, transactions, service interfaces, background tasks, components, errors, traces, config, and health rules
- Offline and mock tests only; no live smoke test is run in this repo

## Setup

```bash
uv sync
uv run ty-apm catalog stats
```

Use environment variables or `config.local.json` for real credentials. `config.local.json` is ignored by git.

```bash
export TY_APM_BASE_URL="https://your-tingyun-host"
export TY_APM_API_KEY="..."
export TY_APM_SECRET_KEY="..."
```

Configuration precedence:

```text
CLI options > environment variables > config.local.json > defaults
```

## Core Commands

```bash
uv run ty-apm catalog list
uv run ty-apm catalog show business_system.2_1.application_business_list
uv run ty-apm catalog search 错误
uv run ty-apm catalog filter --safety read
uv run ty-apm catalog audit-safety

uv run ty-apm auth test
uv run ty-apm auth clear-token

uv run ty-apm api call business_system.2_1.application_business_list \
  --param 'endTime=2026-06-14 20:00:00' \
  --param timePeriod=60
```

Every command writes one JSON envelope to stdout. Non-read calls return an error envelope and do not execute HTTP.

## Artifacts

API calls are archived under:

```text
artifacts/runs/<run_id>/
  run.json
  calls/
  logs/calls.jsonl
```

Use `--run-id` to share a run directory across multiple calls.

## Tests

```bash
uv run pytest
```

The test suite covers catalog schema, safety audit, token mock flow, token cache, redaction, mock read API calls, artifact creation, and non-read refusal.

## Docs

- [Catalog spec](docs/catalog-spec.md)
- [Safety policy](docs/safety-policy.md)
- [Agent output contract](docs/agent-output-contract.md)
- [Testing](docs/testing.md)
- [Company-machine live testing guide](docs/live-testing-on-company-machine.md)
- [Catalog coverage report](docs/catalog-coverage-report.md)

