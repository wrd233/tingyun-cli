# Output Contract

Every command writes exactly one JSON envelope to stdout.

Success:

```json
{"schema_version":"ty-apm.envelope.v1","ok":true,"command":"catalog.list","data":{},"meta":{},"warnings":[]}
```

Failure:

```json
{"schema_version":"ty-apm.envelope.v1","ok":false,"command":"api.call","error":{"type":"SafetyBlocked","message":"v1 only executes safety=read endpoints"},"meta":{},"warnings":[]}
```

Required error types include `ValidationError`, `CatalogNotFound`, `SafetyBlocked`, `AuthError`, `HttpError`, `UpstreamError`, `TimeoutError`, `PartialFailure`, `AmbiguousTarget`, and `InternalError`.

Exit code is `0` for `ok=true` and non-zero for `ok=false`. Failure output remains parseable JSON on stdout. Stderr is empty by default.

Commands include a `catalog_ref` in `meta` when a catalog is loaded:

```json
{"catalog_ref":{"catalog_version":"v1","catalog_commit":"abc1234","catalog_file_hash":"sha256:..."}}
```
