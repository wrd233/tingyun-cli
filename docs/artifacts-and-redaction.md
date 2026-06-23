# Artifacts And Redaction

Secrets redacted:

- `api_key`
- `secret_key`
- `access_token`
- `Authorization`
- `Bearer ...`
- token URL query values

Snapshot JSONL logs contain metadata only. Full request and response bodies are in `calls/*.json` artifacts and may still contain sensitive business facts.

`artifacts/` and `config.local.json` are gitignored.
