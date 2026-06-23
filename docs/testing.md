# Testing

Default tests are offline/mock only:

```bash
PYTHONPATH=src python3 -m pytest -q
```

They cover auth signing source strings, token/redaction behavior, catalog loading and audit, command registration, no raw API command, blocked calls without HTTP, read-call mocks, HTTP errors, upstream business errors, timeouts, lightweight ordinary calls, explicit snapshot profile mappings, plan-only behavior, skipped required params, snapshot package structure, application-context sections, coverage gaps, schema versions, JSONL metadata, and failure exit codes.

Do not put real Tingyun calls in pytest or CI.
