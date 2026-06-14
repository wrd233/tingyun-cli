# Testing

Run:

```bash
uv run pytest
```

Offline tests cover:

- Catalog JSON Schema validation
- Unique catalog ids
- Safety consistency
- Coverage report presence
- Safety audit
- JSON envelope shape
- Redaction

Mock tests cover:

- Token signature calculation
- Token fetch and cache
- Authorization header use
- Read API call through `httpx.MockTransport`
- Request/raw response/envelope/calls log artifact creation
- Non-read refusal before HTTP execution

Live smoke tests are intentionally deferred. Do not add tests that call a real Tingyun host from this development machine.

