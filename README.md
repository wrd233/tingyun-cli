# ty-apm-cli

`ty-apm-cli` is a Tingyun APM Agent-safe read-only API execution layer.

It is the hand, not the brain: it executes catalog-approved read calls, returns structured JSON evidence, and writes bounded snapshot artifacts. It does not diagnose, recommend, generate reports, modify Tingyun state, manage credentials, run a server, or inspect hosts.

## Install

```bash
python3 -m pip install -e .
```

Configure with environment variables or a gitignored `config.local.json`:

```bash
export TY_APM_BASE_URL="https://tingyun.example"
export TY_APM_API_KEY="..."
export TY_APM_SECRET_KEY="..."
```

## Commands

All commands write exactly one JSON envelope to stdout.

```bash
ty-apm catalog list
ty-apm catalog show application.3_1_1.application_app_list
ty-apm catalog search 应用
ty-apm catalog filter --safety read
ty-apm catalog audit-safety

ty-apm auth test
ty-apm auth clear-token

ty-apm api call application.3_1_1.application_app_list --param timePeriod=60

ty-apm resolve application --name "my-app"

ty-apm snapshot collect --profile catalog-smoke --run-id smoke_001
ty-apm snapshot collect --profile inventory --run-id inventory_001
ty-apm snapshot collect --profile health-rules --run-id health_rules_001
ty-apm snapshot collect --profile application-context --application-id 123 --since 60m --run-id app_123_001
```

There is no raw path caller. v1 only executes `safety=read` and `execution_supported=true` catalog entries.

## Artifacts

Only snapshots persist evidence by default under `artifacts/runs/<run_id>/`. Live artifacts can contain sensitive business evidence even after secret redaction. Do not commit, sync, or paste them by default.

## Tests

Default tests are offline/mock only and must not call real Tingyun:

```bash
PYTHONPATH=src python3 -m pytest -q
```
