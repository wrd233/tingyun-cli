# Main Contract Preservation Matrix

| ID | Contract | Main implementation | Donor risk | Integration action/test | Final state |
|---|---|---|---|---|---|
| C01 | Agent-first | CLI receipts/Evidence | depth could dominate | keep Core first in help/docs | CLOSED |
| C02 | immutable Runs | `RunStore` | alternate artifacts | reuse store; local has no Run | CLOSED |
| C03 | source pair | `_resolve_source` | naked IDs | require run+item except explicit alarm list | CLOSED |
| C04 | opaque item ref | Run-local items | fabricated global refs | preserve local refs | CLOSED |
| C05 | exact time | `resolve_time_context` | donor raw time use | reuse resolver | CLOSED |
| C06 | no approximation | time validation | silent widening | block unsupported | CLOSED |
| C07 | FAILED vs EMPTY | execution artifacts | generic extraction | reuse result semantics | CLOSED |
| C08 | PARTIAL Run | coverage overall | donor multi-result drift | source is one fixed step | CLOSED |
| C09 | dynamic Raw provenance | `_derived_from` | static refs | reuse executor result | CLOSED |
| C10 | one transient retry | `HttpExecutor` | alternate executor | no new executor | CLOSED |
| C11 | only 502/503/504 | executor gate | broad retry | unchanged | CLOSED |
| C12 | run-scoped auth recovery | executor state | source loop | one shared executor/run | CLOSED |
| C13 | serial Live | lock/executor | source fanout | one request/source | CLOSED |
| C14 | pacing | executor | bypass builders | execute through executor | CLOSED |
| C15 | strict actions | candidate gates | ranking overexposure | response-only + exact resolver | CLOSED |
| C16 | shared actionType resolver | candidates resolver | donor raw type | reuse resolver | CLOSED |
| C17 | Trace/nav separation | distinct gates | donor URL helper | do not port URL proof | CLOSED |
| C18 | error rate percent | candidate map | donor ratio | keep percent | CLOSED |
| C19 | continuation current Run | collect run id | donor source id | normalize with SOURCE run id | CLOSED |
| C20 | stale inflight recovery | CLI startup | donor dispatch omission | retain startup call | CLOSED |
| C21 | active inflight protection | PID check/lock | early lock | validate then lock | CLOSED |
| C22 | plan-only zero effects | `plan_collect` | workflow storage | pure plan functions | CLOSED |
| C23 | machine-safe invalid plan | local blocked | exceptions | JSON blockers | CLOSED |
| C24 | missing auth preflight | auth gate | donor omission | source auth gate before lock | CLOSED |
| C25 | validation before lock | command ordering | donor lock first | source validates first | CLOSED |
| C26 | logical vs attempts | preflight/manifest | donor single count | expected 1; actual executor sequence | CLOSED |
| C27 | shared pseudonyms | export state | new identities | reuse sanitizer | CLOSED |
| C28 | array identities sanitized | recursive sanitizer | source arrays | leak tests | CLOSED |
| C29 | composite identity sanitized | value replacement | source values | leak tests | CLOSED |
| C30 | Raw responses excluded | export filter | source raw | unchanged filter | CLOSED |
| C31 | internal URLs removed | sanitizer | external URI evidence | source export scan | CLOSED |
| C32 | actions removed | sanitizer | source actions | unchanged key filter | CLOSED |
| C33 | minimized safety | six Core paths | donor broad set | exact formal source registry union | CLOSED |
| C34 | Live-Validated wording | README/reports | stale in-progress | qualified final wording | CLOSED |
| C35 | old Runs immutable | no migration | correction temptation | overlays/local only | CLOSED |

