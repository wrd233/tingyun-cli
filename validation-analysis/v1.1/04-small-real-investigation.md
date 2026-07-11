# v1.1 Small Real Investigation

## Terminal state

`EXTERNALLY_BLOCKED_WITH_PROOF`

The private bundle provides a historical Alarm Seed and prior immutable Live
evidence, but it does not provide a currently configured CLI base URL or a
read-only credential in this process. Environment preflight found
`TINGYUN_BASE_URL` and `TINGYUN_AUTHORIZATION` missing. The production
transport would therefore create only `BLOCKED / AUTH_NOT_CONFIGURED` with
`live_request_count=0`; it cannot execute the required discover -> collect ->
Trace -> Call Tree chain.

Replaying old private responses as though they were a new real investigation
would not prove the upgraded runtime and would misstate Live validation. Trying
another endpoint or bypassing auth/safety would violate the Goal.

## Executable counterpart completed

The full chain was executed with the sanitized immutable replay:

```text
external Alarm Seed
-> exact Window
-> exact Collect Run
-> deterministic Candidate match/binding
-> wrong Trace rejected
-> correct Trace accepted
-> sample assessment
-> target-correct Call Tree
-> evidence compile
-> evidence validate PASS
```

This closes all local selection/composition behavior but is deliberately not
labelled a real Live investigation. When a base URL and read-only credential
become available, the remaining real investigation must use one historical
Seed, serial requests, exact `source_run_id + item_ref`, and the same Manifest;
it must not rerun the full seven-day alarm set.
