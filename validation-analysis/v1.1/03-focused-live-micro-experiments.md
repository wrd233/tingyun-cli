# v1.1 Focused Live Micro-Experiments

## Preflight

Offline prerequisites passed before evaluating Live eligibility: full tests,
protocol consistency, compiler replay, Main-contract re-audit, safety scan, and
credential-presence scan. The scan checked names only and did not print secret
values.

Current environment result:

```text
TINGYUN_BASE_URL=MISSING
TINGYUN_AUTHORIZATION=MISSING
TINGYUN_COOKIE=MISSING
TINGYUN_TOKEN=MISSING
TINGYUN_DATA_ROOT=MISSING
```

Total business requests executed in this v1.1 validation: `0`. Maximum
in-flight observed: `0`. No WRITE/UNKNOWN endpoint was attempted.

## Eligibility decisions

| Experiment | Offline finding | Terminal state | Reason |
|---|---|---|---|
| DubboProvider `TX,IF` direct `actionType=IF` | Exact private structural Candidate exists, but direct IF proof does not; this is the only meaningful contract question | `EXTERNALLY_BLOCKED_WITH_PROOF` | No configured base URL/read-only credential; any request cannot pass auth preflight. Resolver remains unresolved and action hidden. |
| `alarm-events` corrected request | Current POST `/nalarm-api/event/traceList` form body exactly matches 13 historical successful protocol observations for method, path, pagination, time, filters, language, and no required scope | `NOT_APPLICABLE_WITH_PROOF` | Goal allows Live only after an explicit contract delta; no corrected variant exists, so a retry would be brute force. Offline outcome is `PARTIALLY_VERIFIED` for current-environment Live behavior. |
| `application-instances` corrected request | Current POST `/server-api/graph/information` form body exactly matches the observed HTTP 500 request (`bizSystemId`, `applicationId`, time shape, `lang`) | `NOT_APPLICABLE_WITH_PROOF` | No evidence-backed correction exists; repeating the same request is explicitly forbidden. Contract outcome remains `LIVE_CONTRACT_UNRESOLVED`. |
| Verified URL propagation | Sanitized replay contains a verified route and proves Candidate extraction -> Evidence Map -> readiness propagation; guessed proof produces `URL_PROPAGATION_FAILURE` | `NOT_APPLICABLE_WITH_PROOF` | Compiler propagation is closed offline. Private bundle's zero verified URLs is an acquisition gap, not evidence of compiler loss. |

No failed Live request required a repair loop because no Live request was
eligible and executable. The two unresolved external questions are recorded in
`research/protocol/gaps-and-conflicts.md` without expanding runtime safety.
