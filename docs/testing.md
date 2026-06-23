# Testing

Default tests are offline/mock only:

```bash
PYTHONPATH=src python3 -m pytest -q
```

They cover catalog safety, auth signing, redaction, JSON envelopes, blocked calls, read-call mocks, upstream errors, timeouts, snapshot package structure, and JSONL metadata.

Do not put real Tingyun calls in pytest or CI.
