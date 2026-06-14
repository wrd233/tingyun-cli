# Safety Policy

First-version execution is read-only.

Allowed:

- Execute endpoints with `safety=read` and `execution_supported=true`
- Use `POST` read endpoints when the PDF describes query/list/chart/detail behavior
- Fetch tokens through the auth manager

Blocked:

- `guarded`
- `write`
- `unknown`
- Any endpoint whose catalog entry has `execution_supported=false`

The CLI does not expose `--allow-write`, `--allow-guarded`, `--confirm-write`, or any equivalent unlock flag.

Safety classification is conservative. Paths or titles containing create/update/delete/save/bind/unbind/execute/cancel/change/sort semantics are blocked unless they are only cataloged as evidence. `ty-apm catalog audit-safety` must pass before any live read testing.

Credentials, tokens, and Authorization headers are redacted in envelopes and artifacts.

