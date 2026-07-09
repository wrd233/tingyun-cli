# First Live Validation Correction

This report corrects the first controlled Live Golden Path conclusions using existing private evidence only. No live Tingyun requests were made in this closure pass.

## Corrections

| Original normalized result | Raw forensic fact | Root cause | Correction | Current state |
|---|---|---|---|---|
| Topology `EMPTY` | Archived topology Raw contains non-empty live topology wire shape | Normalizer did not read `nodeDataArray` / `linkeDataArray` | Current normalizer reads those keys | Reprocessed as `SUCCESS`, 13 nodes / 38 edges |
| Performance `EMPTY` | Archived performance Raw contains `overviews` and named `series[]` | Normalizer only read earlier simple keys | Current normalizer reads `overviews` and named response/P50/P80/P95/P99 series | Reprocessed as `SUCCESS`, five 30-point series |
| Candidate `error_rate` interpreted as ratio-style example | Wire and exports express error rate as percent | Docs/examples lagged the runtime correction | Runtime and docs use percent | 5% is represented as value `5` |
| Candidate continuation source could be confused with Discovery Run | Candidate item belongs to its creating Collect Run | Earlier docs did not stress Run-local ownership enough | Inspect output preserves Collect `source_run_id` | Agent can copy `source_run_id + item_ref` directly into `investigate` |
| `actionType="TX,IF"` trace request failed and looked like a trace gap | Controlled comparison shows the same candidate succeeds with `actionType="TX"` | Generic composite handling was wrong | Single resolver maps exact `TX,IF -> TX`; unknown composites are withheld | `TX,IF` candidate can trace with `TX`; no generic split rule |
| Sanitized export was described as secret-stripped | Raw response bodies and embedded identities can leak even without secret keys | Sanitizer did not have a whole-export identity pass | Export now uses one pseudonym state and excludes arbitrary Raw responses | External handoff is identity-sanitized and non-executable |
| Startup stale recovery existed but was not wired | `RunStore.freeze_stale_inflight()` existed | CLI startup did not call it | CLI calls recovery before command dispatch | Confirmed stale inflight Runs freeze as `INTERRUPTED` |
| Plan-only invalid input could traceback | Invalid source/time were resolved without local error contract | Expected invalid input was not caught | Plan-only returns machine-readable `BLOCKED` JSON | Zero Run, zero index write, zero HTTP |
| Missing auth could send unauthenticated requests | Default transport only omitted the auth header | No preflight auth block | Default live commands block before HTTP | `BLOCKED / AUTH_NOT_CONFIGURED`, zero HTTP |

## Corrected Project Status

`Golden Path Live-Validated` for the tested target / time window / runtime version.

This does not claim Production-ready, all-domain Live-Proven, or coverage for out-of-scope future capabilities.
