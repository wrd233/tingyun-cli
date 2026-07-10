# Source Capability Promotion Matrix

All executable rows are one bounded serial request producing one immutable SOURCE Run. Verification is existing protocol evidence only; this integration performs zero Live requests.

| Name | Problem | Endpoint/variant | Access | Verification | Required source/identity | Time | Normalizer | Runtime exposure | Promotion |
|---|---|---|---|---|---|---|---|---|---|
| performance-error-series | explicit error series | POST `/server-api/application/charts/error` | READ | VERIFIED protocol | business system / `bizSystemId` | exact frozen | metric series | advanced | PORTED_ADVANCED_READ_ONLY |
| performance-throughput-series | explicit throughput series | POST `/server-api/application/charts/throught` | READ | VERIFIED protocol | business system / `bizSystemId` | exact frozen | metric series | advanced | PORTED_ADVANCED_READ_ONLY |
| alarm-events | bounded alarm list | POST `/nalarm-api/event/traceList` | READ | VERIFIED protocol | explicit list scope; page 1/20 | exact frozen | alarm items | advanced | PORTED_ADVANCED_READ_ONLY |
| alarm-detail | selected alarm facts | POST `/nalarm-api/event/trace` | READ | VERIFIED protocol | alarm event / `alarmEventId` | exact frozen | alarm detail | advanced | PORTED_ADVANCED_READ_ONLY |
| alarm-metric-series | selected alarm metric | POST `/nalarm-api/event/metric/chart` | READ | VERIFIED protocol | complete detail metric/policy/event identity | exact frozen | conservative series | advanced | PORTED_ADVANCED_READ_ONLY |
| recent-requests-response | response ranking/trace entry | POST `/server-api/webaction/list/responseList` | READ | live-verified lineage, scoped | business system / `bizSystemId` | exact frozen | ranked candidates | advanced | PORTED_ADVANCED_READ_ONLY |
| recent-requests-error | error ranking control | POST `/server-api/webaction/list/errorList` | READ | VERIFIED protocol; no trace-lineage inheritance | business system / `bizSystemId` | exact frozen | ranked rows, no actions | advanced | PORTED_ADVANCED_READ_ONLY |
| recent-requests-throughput | throughput ranking control | POST `/server-api/webaction/list/throughtList` | READ | VERIFIED protocol; no trace-lineage inheritance | business system / `bizSystemId` | exact frozen | ranked rows, no actions | advanced | PORTED_ADVANCED_READ_ONLY |
| application-instances | application instance context | POST `/server-api/graph/information` | READ | VERIFIED protocol | application / biz+application IDs | exact frozen | conservative nodes | advanced | PORTED_ADVANCED_READ_ONLY |
| external-calls | external dependency summaries | POST `/server-api/application/ext/uriList` | READ | VERIFIED protocol | application / biz+application IDs | exact frozen | dependency rows | advanced | PORTED_ADVANCED_READ_ONLY |
| trace-exceptions | independent exception evidence | POST `/server-api/action/trace/detail/exceptions` | READ | VERIFIED endpoint; separate from embedded stack | trace / biz+app+actionGuid+traceId+verified actionType | inherited exact | exception rows | advanced | PORTED_ADVANCED_READ_ONLY |
| response performance source | duplicate of Core | POST `/server-api/application/charts/response` | READ | Core Live-validated | business system | exact frozen | existing performance | not duplicated | SUPERSEDED_BY_MAIN |
| component operations | uneven DB/NoSQL/MQ | documented endpoints | READ | partial/documented | incomplete | n/a | none | none | PORTED_RESEARCH_ONLY |
| alarm rule mutation | writes | alarm config endpoints | WRITE | observed protocol | n/a | n/a | none | forbidden | REJECTED_WITH_REASON |

