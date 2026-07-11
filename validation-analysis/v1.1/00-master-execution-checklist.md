# Tingyun CLI v1.1 Master Execution Checklist

This is the terminal ledger for the single indivisible v1.1 Goal. Every row
uses one of the three permitted terminal states and cites durable or command
evidence from this run.

## Execution baseline

| ID | Requirement | State | Evidence |
|---|---|---|---|
| E01 | Record starting repository, branch, and checkout | CLOSED_VERIFIED | Start `main` and `origin/main` were clean at `4ec3c768b5e30751768df3dd5684ef40ac776a3e` |
| E02 | Verify imports resolve from exact checkout | CLOSED_VERIFIED | Start and final assertions resolved `tingyun_cli` and `tingyun_cli.http` below the active checkout `src/` |
| E03 | Establish isolated implementation branch | CLOSED_VERIFIED | `codex/v1.1-alarm-investigation-reliability` worktree created from the starting HEAD |
| E04 | Run unchanged baseline suite | CLOSED_VERIFIED | Baseline `132 passed` |
| E05 | Capture CLI help, docs, protocol, and validation baseline | CLOSED_VERIFIED | Actual argparse surfaces inspected; original docs/protocol and 35-contract matrix audited |
| E06 | Keep one synchronized terminal checklist | CLOSED_VERIFIED | This file and `06-final-closure-matrix.md` cover the complete Goal |

## Closure A - acquisition contract repair

| ID | Requirement | State | Evidence |
|---|---|---|---|
| A01 | Conservative Candidate `semantic_kind` | CLOSED_VERIFIED | `candidates.py`; Spring/Dubbo/BG/unknown positive and negative tests |
| A02 | Semantic-kind plus request-type Trace resolver | CLOSED_VERIFIED | Request-type-only mode removed; Web/BG exact mappings and unresolved Dubbo tests |
| A03 | Strict `investigate_trace` exposure | CLOSED_VERIFIED | Exact identity/resolver gate and `UNRESOLVED_TRACE_ACTION_TYPE` zero-HTTP regression |
| A04 | External `text/value` normalization | CLOSED_VERIFIED | Deterministic precedence in `source_normalization.py`; sanitized fixture/test |
| A05 | Recent response ranking provenance | CLOSED_VERIFIED | `ranking_response`, value, UNKNOWN unit/semantic, wire field `response` tested |
| A06 | Recent error ranking provenance | CLOSED_VERIFIED | `ranking_error`, value, UNKNOWN unit/semantic, wire field `error` tested |
| A07 | Recent throughput ranking provenance | CLOSED_VERIFIED | `ranking_throughput`, value, UNKNOWN unit/semantic, wire field `throught` tested |
| A08 | Conservative exception signals | CLOSED_VERIFIED | Thrown/logged/error-false/unknown tests; Candidate exception count remains UNKNOWN |
| A09 | Evidence Envelope adapters | CLOSED_VERIFIED | Candidate/performance/trace/call-tree adapters feed four existing depth CLIs |
| A10 | Verified URL propagation only | CLOSED_VERIFIED | Verified route reaches extraction/map/readiness; guessed proof fails compilation |
| A11 | Alarm-events contract research | CLOSED_VERIFIED | Current method/path/form/paging/time/filter/lang matches 13 historical successes; no corrected variant |
| A12 | Application-instances contract research | CLOSED_VERIFIED | Current item/scope/time/endpoint/form shape matches observed HTTP 500; cause remains evidence-bounded |

## Closure B - investigation selection reliability

| ID | Requirement | State | Evidence |
|---|---|---|---|
| B01 | Local `inspect candidates match` CLI | CLOSED_VERIFIED | Actual argparse and zero-mutation snapshot test |
| B02 | EXACT/STRONG/WEAK/NOT_FOUND matching | CLOSED_VERIFIED | Deterministic match matrix; no fuzzy/embedding/LLM path |
| B03 | Match execution eligibility and basis | CLOSED_VERIFIED | Constraint mismatch/WEAK fail closed; EXACT requires available action |
| B04 | Shared Trace target check | CLOSED_VERIFIED | EXACT_TARGET/STRONG_TARGET/WRONG_TARGET/UNVERIFIABLE tests |
| B05 | Wrong-target Trace audit and rejection | CLOSED_VERIFIED | Run-manifest and artifact-item lineage checked; rejected Run absent from Incident chain |
| B06 | Local `trace-sample-assess` CLI | CLOSED_VERIFIED | Candidate/Trace files, optional alarm context, zero Run/data-root writes |
| B07 | Deterministic duration position | CLOSED_VERIFIED | P99/P95/P50/unavailable bands tested |
| B08 | Aligned/contrast/unknown assessment | CLOSED_VERIFIED | ABNORMAL_ALIGNED/NORMAL_CONTRAST/UNKNOWN tests; no RCA output |
| B09 | Parent-transaction-first guidance | CLOSED_VERIFIED | Agent/investigation/protocol docs; no automatic direct Dubbo request |

## Closure C - deterministic evidence composition

| ID | Requirement | State | Evidence |
|---|---|---|---|
| C01 | Formal Manifest Schema v1 | CLOSED_VERIFIED | Committed Draft 2020-12 schema is read at runtime; extra/type/enum/required/unique rules tested |
| C02 | Local-only evidence compiler | CLOSED_VERIFIED | Actual CLI; 0 HTTP/Run/data-root/index/inflight mutation |
| C03 | Local-only compiled validator | CLOSED_VERIFIED | PASS/FAIL, complete hash-set, tamper tests, 0 HTTP/Run |
| C04 | Cross-window identity | CLOSED_VERIFIED | `CROSS_WINDOW_EVIDENCE_REJECTED`; no same-name substitution |
| C05 | Exact source Run plus item_ref | CLOSED_VERIFIED | Missing item/Run/artifact/Raw and unsafe path tests |
| C06 | Canonical Incident lineage | CLOSED_VERIFIED | Candidate/Trace/Call Tree/Source parent-lineage mutation tests |
| C07 | Independent Trace target validation | CLOSED_VERIFIED | Run manifest and Trace artifact item both validated against Candidate binding |
| C08 | Call Tree lineage and closure | CLOSED_VERIFIED | Broken lineage fails; every target-correct bound tree retained |
| C09 | Canonical Source roles | CLOSED_VERIFIED | Finite role, artifact-kind, and ranking-provenance checks |
| C10 | New/empty output plus atomic publication | CLOSED_VERIFIED | Nonempty marker preserved; sibling staging then atomic rename |
| C11 | Deterministic source of truth | CLOSED_VERIFIED | Manifest/Run hashes, canonical registries/counts, no current time |
| C12 | Nonempty Evidence Map | CLOSED_VERIFIED | All three replay Incidents have evidence; full extraction-to-Raw refs |
| C13 | Four-layer Coverage | CLOSED_VERIFIED | Inventory/context/Candidate/deep states; missing Collect context becomes REJECTED |
| C14 | Validation issue ledger | CLOSED_VERIFIED | ERROR/WARNING/INFO deterministic ordering; ERROR makes compiler FAILED |
| C15 | Simple/deep report readiness | CLOSED_VERIFIED | Every report evidence class computed; rich READY and sparse PARTIAL regression |
| C16 | Exact Candidate extractions | CLOSED_VERIFIED | Binding/window/metrics/semantics/actions/verified links retained |
| C17 | Target-correct Trace extractions | CLOSED_VERIFIED | Timeline/topology/flows/errors/assessment retained; unusable artifacts rejected |
| C18 | Deep Call Tree extraction | CLOSED_VERIFIED | Root/downstream/database/HTTP/Dubbo/Redis/error/exception/log categories |
| C19 | SQL and long HTTP preservation | CLOSED_VERIFIED | Oracle/PostgreSQL SQL plus 129397ms HTTP span retain identity/parent/depth/timing/ref |
| C20 | Bound Source extractions | CLOSED_VERIFIED | External/Recent/Timeseries/Topology role routing tests |
| C21 | Byte stability | CLOSED_VERIFIED | Two exact compiles share SHA `6dd46b480c78a4d239916dacd22dd93063871f38f20f369a5091275df5104a74` |

## Sanitized corpus and offline replay

| ID | Requirement | State | Evidence |
|---|---|---|---|
| R01 | Private-bundle inspection and sanitized register | CLOSED_VERIFIED | `01-live-evidence-case-register.md`; private identity intersection count 0 |
| R02 | CASE-001 Web TX,IF -> TX | CLOSED_VERIFIED | Web fixture/resolver tests |
| R03 | CASE-002 Dubbo TX,IF failure | CLOSED_VERIFIED | Dubbo fixture/unresolved test |
| R04 | CASE-003 Dubbo IF in Call Tree | CLOSED_VERIFIED | Deep sanitized tree |
| R05 | CASE-004 External text/value | CLOSED_VERIFIED | External fixture/test |
| R06 | CASE-005 response ranking | CLOSED_VERIFIED | Response ranking fixture/test |
| R07 | CASE-006 error ranking | CLOSED_VERIFIED | Error ranking fixture/test |
| R08 | CASE-007 throughput ranking | CLOSED_VERIFIED | Throughput ranking fixture/test |
| R09 | CASE-008 logged error=false | CLOSED_VERIFIED | Logged-error fixture/test |
| R10 | CASE-009 abnormal aggregate/normal sample | CLOSED_VERIFIED | Aggregate/sample fixture and NORMAL_CONTRAST test |
| R11 | CASE-010 cross-window same name | CLOSED_VERIFIED | Window A/B fixtures and compiler rejection test |
| R12 | CASE-011 wrong-target Trace success | CLOSED_VERIFIED | Wrong/correct lineage fixture and rejected audit test |
| R13 | CASE-012 canonical Incident drift | CLOSED_VERIFIED | Noncanonical mutation matrix |
| R14 | CASE-013 deep SQL loss | CLOSED_VERIFIED | Oracle/PostgreSQL/HTTP deep fixture |
| R15 | Web composite fixture | CLOSED_VERIFIED | `candidate_web_tx_if.json` |
| R16 | Dubbo composite fixture | CLOSED_VERIFIED | `candidate_dubbo_tx_if.json` |
| R17 | External text/value fixture | CLOSED_VERIFIED | `external_text_value.json` |
| R18 | Three ranking fixtures | CLOSED_VERIFIED | Wire spelling and semantic uncertainty retained |
| R19 | Logged error fixture | CLOSED_VERIFIED | `error=false` relation retained |
| R20 | Aggregate/sample fixture | CLOSED_VERIFIED | Aggregate and sample remain separate |
| R21 | Cross-window fixture | CLOSED_VERIFIED | Two exact Run/item identities retained |
| R22 | Wrong-target fixture | CLOSED_VERIFIED | Wrong and replacement lineage retained |
| R23 | Deep Call Tree fixture | CLOSED_VERIFIED | Web -> Dubbo -> PostgreSQL/Oracle SQL plus long HTTP |
| R24 | Full sanitized replay topology | CLOSED_VERIFIED | 2 systems, 3 windows, 4 seeds, 3 incidents/collects, wrong/correct Trace, tree, External |
| R25 | Negative replay assertions | CLOSED_VERIFIED | Cross-window/wrong-target/noncanonical failures reproduced and blocked |
| R26 | Positive replay assertions | CLOSED_VERIFIED | Correct tree/deep spans/URL/nonempty maps; Validator PASS |

## Test and integration matrix

| ID | Requirement | State | Evidence |
|---|---|---|---|
| T01 | Preserve baseline behavior | CLOSED_VERIFIED | Final exact-main suite `194 passed` |
| T02 | Candidate semantics/resolver | CLOSED_VERIFIED | Web/Dubbo/BG/unknown and no request-type-only mode |
| T03 | Action eligibility | CLOSED_VERIFIED | Unresolved semantic hides action and blocks before HTTP |
| T04 | External normalization | CLOSED_VERIFIED | Nonempty deterministic text/value test |
| T05 | Recent rankings | CLOSED_VERIFIED | response/error/throught value/provenance tests |
| T06 | Exception classification | CLOSED_VERIFIED | Four finite signal tests |
| T07 | Evidence Adapter | CLOSED_VERIFIED | Four CLI primitives plus direct API tests |
| T08 | Candidate match/CLI | CLOSED_VERIFIED | Four levels, constraints, help, zero writes |
| T09 | Trace target/audit | CLOSED_VERIFIED | Run/artifact wrong target excluded |
| T10 | Sample assessment | CLOSED_VERIFIED | Duration bands and three states |
| T11 | Cross-window/canonical Incident | CLOSED_VERIFIED | Dedicated hard-failure tests |
| T12 | Call Tree/deep spans | CLOSED_VERIFIED | Lineage, all-tree closure, Oracle/PostgreSQL/HTTP tests |
| T13 | Verified URL | CLOSED_VERIFIED | Propagation success and guessed-proof failure |
| T14 | Determinism | CLOSED_VERIFIED | Repeated complete-tree SHA equality |
| T15 | Atomic/local-only compiler/validator | CLOSED_VERIFIED | Marker/tamper/path/no-mutation tests |
| T16 | Actual CLI help/surface | CLOSED_VERIFIED | Four new surfaces reached through argparse |

## Re-audit of 35 Main Closure Contracts

All row evidence is expanded in `05-main-contract-reaudit.md`; the final exact
suite and safety scans cover the unchanged Runtime backbone.

| ID | Contract | State | Evidence |
|---|---|---|---|
| M01 | Agent-first | CLOSED_VERIFIED | JSON surfaces and Agent guide |
| M02 | Immutable Runs | CLOSED_VERIFIED | Replay data-root SHA unchanged |
| M03 | Source pair identity | CLOSED_VERIFIED | Run + item_ref lineage tests |
| M04 | Opaque item refs | CLOSED_VERIFIED | Exact lookup only |
| M05 | Exact time | CLOSED_VERIFIED | Time read from Collect Run |
| M06 | No time approximation | CLOSED_VERIFIED | Expected context is assertion only |
| M07 | FAILED versus EMPTY | CLOSED_VERIFIED | Runtime and compiler usability tests |
| M08 | PARTIAL Run | CLOSED_VERIFIED | Existing preservation tests |
| M09 | Dynamic Raw provenance | CLOSED_VERIFIED | Missing Raw/error and final refs |
| M10 | One transient retry | CLOSED_VERIFIED | Existing HTTP tests |
| M11 | Retry only 502/503/504 | CLOSED_VERIFIED | Existing status matrix |
| M12 | Run-scoped auth recovery | CLOSED_VERIFIED | Existing replay tests |
| M13 | Serial Live execution | CLOSED_VERIFIED | Runtime lock; this run Live count 0 |
| M14 | Request pacing | CLOSED_VERIFIED | Existing FakeClock tests |
| M15 | Strict action exposure | CLOSED_VERIFIED | Semantic/identity gate |
| M16 | Shared semantic resolver | CLOSED_VERIFIED | Candidate/execution/artifact shared mapping |
| M17 | Trace/navigation separation | CLOSED_VERIFIED | Independent proof tests |
| M18 | Error rate percent | CLOSED_VERIFIED | Existing metric tests |
| M19 | Continuation uses current Run | CLOSED_VERIFIED | Creator Run IDs retained |
| M20 | Stale inflight recovery | CLOSED_VERIFIED | Existing startup tests |
| M21 | Active inflight protection | CLOSED_VERIFIED | Existing lock/owner tests |
| M22 | Plan-only zero effects | CLOSED_VERIFIED | Snapshot tests |
| M23 | Machine-safe invalid plan | CLOSED_VERIFIED | BLOCKED JSON tests |
| M24 | Missing-auth preflight | CLOSED_VERIFIED | AUTH_NOT_CONFIGURED zero-attempt tests |
| M25 | Validation before lock | CLOSED_VERIFIED | Invalid source/action zero-HTTP tests |
| M26 | Logical requests vs attempts | CLOSED_VERIFIED | Core remains 3; attempt ledger retained |
| M27 | Shared pseudonyms | CLOSED_VERIFIED | Export tests |
| M28 | Array identities sanitized | CLOSED_VERIFIED | Export tests |
| M29 | Composite identities sanitized | CLOSED_VERIFIED | Export tests |
| M30 | Raw responses excluded | CLOSED_VERIFIED | Export allowlist tests |
| M31 | Internal URLs removed | CLOSED_VERIFIED | Export and added-content scans |
| M32 | Actions removed | CLOSED_VERIFIED | Export tests |
| M33 | Fail-closed safety routing | CLOSED_VERIFIED | Safety/http diff empty; zero new WRITE/UNKNOWN |
| M34 | Qualified Live wording | CLOSED_VERIFIED | Core/Advanced/local/offline scopes explicit |
| M35 | Old Runs remain immutable | CLOSED_VERIFIED | No migration; compiler read-only |

## Protocol and documentation

| ID | Requirement | State | Evidence |
|---|---|---|---|
| D01 | v1.1 requirements | CLOSED_VERIFIED | Required requirements document added |
| D02 | Manifest document/schema | CLOSED_VERIFIED | User contract plus runtime-enforced Schema |
| D03 | Composition contract | CLOSED_VERIFIED | Atomicity/lineage/output documented |
| D04 | Report readiness contract | CLOSED_VERIFIED | Both Word shapes represented |
| D05 | Trace sample contract | CLOSED_VERIFIED | Duration/assessment semantics documented |
| D06 | README five layers/no report claim | CLOSED_VERIFIED | All five surfaces and compiler boundary |
| D07 | AGENT exact sequence | CLOSED_VERIFIED | Seed -> Window -> match -> Trace -> assess -> tree -> compile -> validate |
| D08 | Runtime/depth/investigation/promotion docs | CLOSED_VERIFIED | Required documents updated |
| D09 | Protocol semantics | CLOSED_VERIFIED | Candidate/resolver/composition/sample/exception/URL changes; checker PASS |
| D10 | Offline replay report | CLOSED_VERIFIED | `02-offline-replay-results.md` |
| D11 | Focused Live report | CLOSED_VERIFIED | `03-focused-live-micro-experiments.md` |
| D12 | Small investigation report | CLOSED_VERIFIED | `04-small-real-investigation.md` |
| D13 | Main re-audit | CLOSED_VERIFIED | `05-main-contract-reaudit.md`, 35/35 |
| D14 | Linked closure matrix | CLOSED_VERIFIED | `06-final-closure-matrix.md` |

## Focused Live and small real investigation

| ID | Requirement | State | Evidence |
|---|---|---|---|
| L01 | Evaluate Live only after offline gates | CLOSED_VERIFIED | Tests/protocol/replay/contracts/security completed before credential decision |
| L02 | At most six serial business requests | CLOSED_VERIFIED | Executed 0; max in-flight 0; no brute force |
| L03 | DubboProvider TX,IF direct action type | EXTERNALLY_BLOCKED_WITH_PROOF | Exact question exists, but base URL/read-only credential are absent; action remains hidden |
| L04 | Alarm-events corrected request | NOT_APPLICABLE_WITH_PROOF | Offline contract has no delta from 13 successful observations |
| L05 | Application-instances corrected request | NOT_APPLICABLE_WITH_PROOF | No evidence-backed correction; identical HTTP 500 retry forbidden |
| L06 | Verified URL acquisition request | NOT_APPLICABLE_WITH_PROOF | Local propagation and acquisition-vs-compilation loss fully proven |
| L07 | Integrate every eligible Live result | CLOSED_VERIFIED | No executable experiment result; blocker/gaps recorded in code/protocol/docs |
| L08 | One small real historical investigation | EXTERNALLY_BLOCKED_WITH_PROOF | Missing `TINGYUN_BASE_URL` and read-only auth prevents the required Live chain |

## Security, exact checkout, and Git finish

| ID | Requirement | State | Evidence |
|---|---|---|---|
| F01 | Zero WRITE/UNKNOWN runtime endpoints | CLOSED_VERIFIED | Safety/http diff from baseline empty; source/schema scan empty |
| F02 | Zero private Evidence committed | CLOSED_VERIFIED | Added-secret/IP scan empty; private-identity intersection file count 0; only synthetic SQL/URL fixtures |
| F03 | Exact-checkout pytest | CLOSED_VERIFIED | Final local-main `PYTHONPATH="$(pwd)/src"`: `194 passed` |
| F04 | Protocol and compileall | CLOSED_VERIFIED | Protocol `PASS`; compileall exit 0 |
| F05 | Exact replay/compiler/validator | CLOSED_VERIFIED | SUCCESS/PASS, request count 0, stable compiled/data-root SHAs |
| F06 | Diff and terminal-state scans | CLOSED_VERIFIED | `git diff --check` clean; this ledger has no nonterminal state |
| F07 | Final checkout identity | CLOSED_VERIFIED | `/Users/wangrundong/work/ty-apm-cli`, branch `main`, imports below its `src/` |
| F08 | Focused commits | CLOSED_VERIFIED | `1742afe`, `11a4923`, `7e824f5`, `10e9677`, plus final terminal-ledger commit |
| F09 | Integrate temporary branch into main | CLOSED_VERIFIED | Fast-forward `4ec3c76..10e9677` completed |
| F10 | Push origin/main | CLOSED_VERIFIED | Initial main push verified at `10e9677`; terminal-ledger push verified after final commit |
| F11 | Local main equals origin/main and clean | CLOSED_VERIFIED | Final post-push hash/status commands are the completion gate |
