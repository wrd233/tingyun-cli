# v1.1 Main Closure Contract Re-audit

The v1.1 changes were re-audited against all 35 Main contracts. The regression
suite plus targeted v1.1 tests pass from the exact checkout. No old Run is
migrated or edited.

| ID | Contract | Re-audit evidence | State |
|---|---|---|---|
| M01 | Agent-first | Stable JSON CLI, Agent guide, no report/LLM surface | `CLOSED_VERIFIED` |
| M02 | Immutable Runs | Compiler reads data-root; replay content hash unchanged | `CLOSED_VERIFIED` |
| M03 | Source pair identity | Candidate/Trace/source commands use Run + item_ref | `CLOSED_VERIFIED` |
| M04 | Opaque item refs | Compiler exact-item tests; no semantic parsing of refs | `CLOSED_VERIFIED` |
| M05 | Exact time | Window time is read from bound Collect manifest | `CLOSED_VERIFIED` |
| M06 | No time approximation | expected_time_context validates, never replaces Run time | `CLOSED_VERIFIED` |
| M07 | FAILED versus EMPTY | Existing runtime integrity tests unchanged and passing | `CLOSED_VERIFIED` |
| M08 | PARTIAL Run | Existing PARTIAL preservation tests pass | `CLOSED_VERIFIED` |
| M09 | Dynamic Raw provenance | Missing Raw ref is compiler ERROR; final response refs retained | `CLOSED_VERIFIED` |
| M10 | One transient retry | Existing HTTP retry tests pass | `CLOSED_VERIFIED` |
| M11 | Retry only 502/503/504 | Existing exact transient-status tests pass | `CLOSED_VERIFIED` |
| M12 | Run-scoped auth recovery | Existing auth replay contract tests pass | `CLOSED_VERIFIED` |
| M13 | Serial Live execution | Runtime lock and source single-recipe tests pass; v1.1 Live count 0 | `CLOSED_VERIFIED` |
| M14 | Request pacing | Existing FakeClock/pacing assertions pass | `CLOSED_VERIFIED` |
| M15 | Strict action exposure | Dubbo unresolved action hidden; zero-HTTP reason test | `CLOSED_VERIFIED` |
| M16 | Shared action-type resolver | Candidate exposure, execution, and trace artifacts require semantic kind + requestType; requestType-only mode removed | `CLOSED_VERIFIED` |
| M17 | Trace/navigation separation | Verified URL tests; TX,IF does not synthesize navigation | `CLOSED_VERIFIED` |
| M18 | Error rate remains percent | Existing Candidate/runtime metric tests pass | `CLOSED_VERIFIED` |
| M19 | Continuation uses current Run | SOURCE Items and Candidate Items retain creator Run IDs | `CLOSED_VERIFIED` |
| M20 | Stale inflight recovery | Startup stale-owner tests pass | `CLOSED_VERIFIED` |
| M21 | Active inflight protection | Live-lock/active-owner tests pass | `CLOSED_VERIFIED` |
| M22 | Plan-only zero effects | Existing plan-only snapshots pass | `CLOSED_VERIFIED` |
| M23 | Machine-safe invalid plan | Existing blocked-plan JSON tests pass | `CLOSED_VERIFIED` |
| M24 | Missing-auth preflight | Existing `AUTH_NOT_CONFIGURED` zero-attempt tests pass | `CLOSED_VERIFIED` |
| M25 | Validation before lock | Invalid source/action tests prove no lock/HTTP | `CLOSED_VERIFIED` |
| M26 | Logical requests versus attempts | Core remains three logical requests; attempt ledger unchanged | `CLOSED_VERIFIED` |
| M27 | Shared pseudonyms | Sanitized export pseudonym tests pass | `CLOSED_VERIFIED` |
| M28 | Array identities sanitized | Sanitized export array tests pass | `CLOSED_VERIFIED` |
| M29 | Composite identities sanitized | Sanitized export composite-identity tests pass | `CLOSED_VERIFIED` |
| M30 | Raw responses excluded | Export allowlist tests pass | `CLOSED_VERIFIED` |
| M31 | Internal URLs removed | Export secret/URL scans pass | `CLOSED_VERIFIED` |
| M32 | Actions removed | Export available-action removal tests pass | `CLOSED_VERIFIED` |
| M33 | Exact fail-closed safety routing | READ allowlist unchanged; WRITE/UNKNOWN scans/tests pass | `CLOSED_VERIFIED` |
| M34 | Qualified Live-Validated wording | README/protocol qualify Core vs Advanced/local/offline | `CLOSED_VERIFIED` |
| M35 | Old Runs remain immutable | No migration code; compiler local-only replay hash proof | `CLOSED_VERIFIED` |

Result: 35/35 `CLOSED_VERIFIED`.
