# Design Decisions

- v1 is a deep read-only factual evidence layer.
- Catalog IDs are the only execution route.
- `POST` endpoints can be read only when the manual describes query/list/detail/chart behavior.
- Risky side-effect wording is conservatively blocked.
- Ordinary `api call` is stdout-only by default.
- Snapshot profiles are built in; no external workflow/profile DSL.
- `application-context` is fixed, bounded, and factual.
- Credentials, tokens, and Authorization headers are always redacted.
- Default tests are offline/mock only.
