# Main Contract Preservation Matrix

| ID | Contract | Main implementation | Donor risk | Integration action/test | Final state |
|---|---|---|---|---|---|
| C01 | Agent-first | CLI receipts/Evidence | depth could dominate | keep Core first in help/docs | pending verify |
| C02 | immutable Runs | `RunStore` | alternate artifacts | reuse store; local has no Run | pending verify |
| C03 | source pair | `_resolve_source` | naked IDs | require run+item except explicit alarm list | pending verify |
| C04 | opaque item ref | Run-local items | fabricated global refs | preserve local refs | pending verify |
| C05 | exact time | `resolve_time_context` | donor raw time use | reuse resolver | pending verify |
| C06 | no approximation | time validation | silent widening | block unsupported | pending verify |
| C07 | FAILED vs EMPTY | execution artifacts | generic extraction | reuse result semantics | pending verify |
| C08 | PARTIAL Run | coverage overall | donor multi-result drift | source is one fixed step | pending verify |
| C09 | dynamic Raw provenance | `_derived_from` | static refs | reuse executor result | pending verify |
| C10 | one transient retry | `HttpExecutor` | alternate executor | no new executor | pending verify |
| C11 | only 502/503/504 | executor gate | broad retry | unchanged | pending verify |
| C12 | run-scoped auth recovery | executor state | source loop | one shared executor/run | pending verify |
| C13 | serial Live | lock/executor | source fanout | one request/source | pending verify |
| C14 | pacing | executor | bypass builders | execute through executor | pending verify |
| C15 | strict actions | candidate gates | ranking overexposure | response-only + exact resolver | pending verify |
| C16 | shared actionType resolver | candidates resolver | donor raw type | reuse resolver | pending verify |
| C17 | Trace/nav separation | distinct gates | donor URL helper | do not port URL proof | pending verify |
| C18 | error rate percent | candidate map | donor ratio | keep percent | pending verify |
| C19 | continuation current Run | collect run id | donor source id | normalize with SOURCE run id | pending verify |
| C20 | stale inflight recovery | CLI startup | donor dispatch omission | retain startup call | pending verify |
| C21 | active inflight protection | PID check/lock | early lock | validate then lock | pending verify |
| C22 | plan-only zero effects | `plan_collect` | workflow storage | pure plan functions | pending verify |
| C23 | machine-safe invalid plan | local blocked | exceptions | JSON blockers | pending verify |
| C24 | missing auth preflight | auth gate | donor omission | source auth gate before lock | pending verify |
| C25 | validation before lock | command ordering | donor lock first | source validates first | pending verify |
| C26 | logical vs attempts | preflight/manifest | donor single count | expected 1; actual executor sequence | pending verify |
| C27 | shared pseudonyms | export state | new identities | reuse sanitizer | pending verify |
| C28 | array identities sanitized | recursive sanitizer | source arrays | leak tests | pending verify |
| C29 | composite identity sanitized | value replacement | source values | leak tests | pending verify |
| C30 | Raw responses excluded | export filter | source raw | unchanged filter | pending verify |
| C31 | internal URLs removed | sanitizer | external URI evidence | source export scan | pending verify |
| C32 | actions removed | sanitizer | source actions | unchanged key filter | pending verify |
| C33 | minimized safety | six Core paths | donor broad set | exact formal source registry union | pending verify |
| C34 | Live-Validated wording | README/reports | stale in-progress | qualified final wording | pending verify |
| C35 | old Runs immutable | no migration | correction temptation | overlays/local only | pending verify |

