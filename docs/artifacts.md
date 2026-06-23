# Artifacts

Ordinary API calls do not create run directories by default. They return one JSON envelope to stdout.

Snapshot `--plan-only` also does not create run directories. It returns a JSON envelope with the planned calls and parameter sources.

Snapshot commands create evidence packages under:

```text
artifacts/runs/<run_id>/
  run.json
  logs/calls.jsonl
  calls/
    call_0001.request.json
    call_0001.response.json
  snapshot/
    manifest.json
    summary.json
    coverage.json
    sections/
```

Request and response artifacts are redacted for credentials and bearer tokens, but they may still contain sensitive business evidence. Treat `artifacts/` as local sensitive data. Do not commit, sync, or paste live artifacts by default.

`logs/calls.jsonl` contains metadata only, not full request or response bodies.

The access-token cache is a separate runtime cache (`.ty-apm-token-cache.json` by default, or `TY_APM_TOKEN_CACHE_PATH`) and is not a snapshot evidence artifact.
