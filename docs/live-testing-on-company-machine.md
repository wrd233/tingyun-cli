# Live Testing On Company Machine

This repository only performs offline and mock tests. Real Tingyun access should be tested later on a company-network machine, for example with Claude Code, using a separate results directory.

Before any live call:

```bash
uv run ty-apm catalog audit-safety
uv run pytest
```

Rules:

- Only call `safety=read` endpoints.
- Do not call `guarded`, `write`, or `unknown`.
- Do not pass around token, secret, Authorization header, or sensitive business data.
- Save live results independently, for example with `--output-dir ./artifacts-live-readonly`.
- Do not automatically write live results back into the main catalog.
- Use `--run-id` to group a small, explicit live-read session.

Suggested first live smoke:

```bash
uv run ty-apm --run-id live_read_001 catalog audit-safety
uv run ty-apm --run-id live_read_001 auth test
uv run ty-apm --run-id live_read_001 business-system list --time-period 60
```

Stop immediately if any command returns `ok=false` with a safety, auth, or HTTP error that is not understood.

