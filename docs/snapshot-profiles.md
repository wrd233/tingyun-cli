# Snapshot Profiles

Supported v1 profiles:

- `catalog-smoke`: small read-only execution smoke.
- `inventory`: bounded platform inventory.
- `health-rules`: read-only health rule inventory.
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
