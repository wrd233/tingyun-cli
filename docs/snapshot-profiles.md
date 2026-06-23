# Snapshot Profiles

Supported v1 profiles:

- `catalog-smoke`: minimal live-readiness check using a fixed, explicit list of low-risk read endpoints. It is not business validation.
- `inventory`: bounded global read-only inventory, avoiding high-volume trace/error detail.
- `health-rules`: read-only health rule list/detail evidence where safe.
- `application-context`: bounded factual portrait for one application.

Snapshots are sequential by default and write:

```text
artifacts/runs/<run_id>/
  run.json
  logs/calls.jsonl
  calls/
  snapshot/manifest.json
  snapshot/summary.json
  snapshot/coverage.json
  snapshot/sections/
```

Snapshot JSON files use fixed schema versions:

- `ty-apm.run.v1`
- `ty-apm.call_log.v1`
- `ty-apm.snapshot.manifest.v1`
- `ty-apm.snapshot.summary.v1`
- `ty-apm.snapshot.coverage.v1`
- `ty-apm.snapshot.section.v1`

Coverage records each requested section as completed, failed, skipped, or blocked, with gaps such as `upstream_error`, `http_error`, `safety_blocked`, `missing_required_param`, `not_implemented`, and `failed`.

Preview a profile without HTTP or artifacts:

```bash
ty-apm snapshot collect --profile catalog-smoke --plan-only
ty-apm snapshot collect --profile application-context --application-id 123 --plan-only
```

Plan-only output lists planned sections, catalog IDs, safety/execution flags, parameter values, parameter sources, and skipped steps. Snapshot profiles are code-defined only; there is no external YAML/JSON workflow DSL.
