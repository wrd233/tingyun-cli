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

Exit code is `0` for `ok=true` and non-zero for `ok=false`.
