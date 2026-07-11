# v1.1 Final Closure Matrix

## Closure A - Acquisition Contract Repair

| ID | Deliverable | Code / evidence | Tests / documentation | State |
|---|---|---|---|---|
| A01 | Candidate semantic kind | `candidates.py`; Web/Dubbo fixtures | `test_v1_1_semantics.py`; requirements | `CLOSED_VERIFIED` |
| A02 | Trace action resolver | semantic kind + requestType resolver; unresolved reason | shared resolver and zero-HTTP tests | `CLOSED_VERIFIED` |
| A03 | Strict Trace action exposure | exact wire identity + resolver gate | old malicious-action and new Dubbo tests | `CLOSED_VERIFIED` |
| A04 | External text/value normalization | `source_normalization.py` deterministic precedence | External fixture/test; case register | `CLOSED_VERIFIED` |
| A05 | Recent response ranking | value + `response` provenance | response fixture/test | `CLOSED_VERIFIED` |
| A06 | Recent error ranking | value + `error` provenance | error fixture/test | `CLOSED_VERIFIED` |
| A07 | Recent throughput ranking | value + `throught` provenance | throughput fixture/test | `CLOSED_VERIFIED` |
| A08 | Exception classification | four finite signals; candidate count UNKNOWN | logged-error fixture/four-state tests | `CLOSED_VERIFIED` |
| A09 | Evidence Envelope adapter | Candidate/performance/trace/call-tree views | direct API and four CLI primitive tests | `CLOSED_VERIFIED` |
| A10 | Verified URL propagation | compiler proof allowlist and failure code | replay + guessed-link failure test | `CLOSED_VERIFIED` |
| A11 | Alarm request contract | exact offline comparison with 13 historical successes | protocol metadata; Live report | `CLOSED_VERIFIED` |
| A12 | Instance request contract | exact same-shape HTTP 500 comparison, no unsupported interpretation | protocol gap; Live report | `CLOSED_VERIFIED` |

## Closure B - Investigation Selection Reliability

| ID | Deliverable | Code / evidence | Tests / documentation | State |
|---|---|---|---|---|
| B01 | `inspect candidates match` | `candidate_matching.py`, CLI | local snapshot/no-write test | `CLOSED_VERIFIED` |
| B02 | Match levels | EXACT/STRONG/WEAK/NOT_FOUND deterministic rules | match matrix tests | `CLOSED_VERIFIED` |
| B03 | Execution eligibility | constraint mismatch and WEAK fail closed | eligibility tests | `CLOSED_VERIFIED` |
| B04 | Trace target check | `investigation_selection.py` | exact/wrong/unverifiable tests | `CLOSED_VERIFIED` |
| B05 | Wrong-target audit/rejection | compiler rejected ledger | replay and Evidence Map assertions | `CLOSED_VERIFIED` |
| B06 | Trace sample CLI | `trace_sample_assessment.py`, CLI | local/no-write test | `CLOSED_VERIFIED` |
| B07 | Duration position | P99/P95/P50/unavailable bands | abnormal/normal/unknown tests | `CLOSED_VERIFIED` |
| B08 | Sample assessment | aligned/contrast/unknown, no RCA | fixture/compiler shared-logic tests | `CLOSED_VERIFIED` |
| B09 | Parent-transaction-first guidance | plan/docs only, no auto-execution | Agent/investigation/protocol docs | `CLOSED_VERIFIED` |

## Closure C - Deterministic Evidence Composition

| ID | Deliverable | Code / evidence | Tests / documentation | State |
|---|---|---|---|---|
| C01 | Manifest schema v1 | formal JSON Schema read and enforced at runtime | schema/extra/type/enum/malformed tests; manifest doc | `CLOSED_VERIFIED` |
| C02 | Local compiler CLI | `evidence_composition.py`, atomic output | local/no-mutation replay | `CLOSED_VERIFIED` |
| C03 | Local validator CLI | `evidence_validation.py` | PASS/tamper tests | `CLOSED_VERIFIED` |
| C04 | Cross-window validation | exact Window/Collect check | same-name mutation test | `CLOSED_VERIFIED` |
| C05 | Exact item validation | source Run + item_ref | missing item/Run/artifact tests | `CLOSED_VERIFIED` |
| C06 | Canonical Incident validation | parent-lineage checks for all binding kinds | four mutation classes | `CLOSED_VERIFIED` |
| C07 | Trace target validation | independent Run manifest and artifact-item source checks | wrong Trace warning/exclusion | `CLOSED_VERIFIED` |
| C08 | Call Tree closure | manifest + artifact lineage; all correct trees retained | broken/two-tree tests | `CLOSED_VERIFIED` |
| C09 | Source role validation | finite roles, artifact kind/ranking match | mismatch and routing tests | `CLOSED_VERIFIED` |
| C10 | Atomic/new output | sibling staging + replace, no overwrite | marker preservation test | `CLOSED_VERIFIED` |
| C11 | Source of truth | canonical registries, hashes, counts | replay exact counts | `CLOSED_VERIFIED` |
| C12 | Evidence Map | full Incident chain + rejected audit | all three maps nonempty | `CLOSED_VERIFIED` |
| C13 | Four-layer coverage | inventory/context/Candidate/deep | replay output | `CLOSED_VERIFIED` |
| C14 | Validation ledger | ERROR/WARNING/INFO ordering and failure semantics | negative matrix | `CLOSED_VERIFIED` |
| C15 | Report readiness | every simple/deep evidence class derived from accepted evidence | readiness doc/rich READY/sparse PARTIAL tests | `CLOSED_VERIFIED` |
| C16 | Candidate extractions | exact Window/binding metrics/semantic/actions/links | replay assertions | `CLOSED_VERIFIED` |
| C17 | Trace extractions | target-correct timeline/topology/flows/errors/assessment | compiler tests | `CLOSED_VERIFIED` |
| C18 | Deep Call Tree | all spans and typed categories | six-node fixture | `CLOSED_VERIFIED` |
| C19 | SQL/long HTTP preservation | parent/depth/timing/ref and exclusive ranking | Oracle/PostgreSQL SQL + 129397ms assertions | `CLOSED_VERIFIED` |
| C20 | Source extractions | External/Recent/Timeseries/Topology role routing | bound-source routing test | `CLOSED_VERIFIED` |
| C21 | Determinism | stable ordering/hashes/no dynamic fields | identical tree hash replay | `CLOSED_VERIFIED` |

## Live and finish gates

| Gate | State | Evidence |
|---|---|---|
| Focused Dubbo direct Trace | `EXTERNALLY_BLOCKED_WITH_PROOF` | missing base URL/read-only auth; action remains hidden |
| Alarm corrected request | `NOT_APPLICABLE_WITH_PROOF` | no offline contract delta |
| Instance corrected request | `NOT_APPLICABLE_WITH_PROOF` | no evidence-backed correction; identical retry forbidden |
| URL propagation request | `NOT_APPLICABLE_WITH_PROOF` | local acquisition/propagation distinction fully proven |
| Small real investigation | `EXTERNALLY_BLOCKED_WITH_PROOF` | production auth preflight cannot execute Live chain |
| Offline replay | `CLOSED_VERIFIED` | compiler SUCCESS, validator PASS, zero HTTP/Run/mutation |
| Main contracts | `CLOSED_VERIFIED` | 35/35 re-audit |

Git/exact-checkout hashes and final clean/push proof are recorded in the Master
Execution Checklist after integration.
