# Tingyun CLI v1.1 Master Execution Checklist

This ledger covers the single indivisible v1.1 Goal. Every row must end as
`CLOSED_VERIFIED`, `EXTERNALLY_BLOCKED_WITH_PROOF`, or
`NOT_APPLICABLE_WITH_PROOF` before the final response.

## Execution baseline

| ID | Requirement | State | Evidence |
|---|---|---|---|
| E01 | Record starting repository, branch, and checkout | CLOSED_VERIFIED | Starting HEAD `4ec3c768b5e30751768df3dd5684ef40ac776a3e`; clean `main`; `main == origin/main` |
| E02 | Verify imports resolve from the exact checkout | CLOSED_VERIFIED | `tingyun_cli` and `tingyun_cli.http` resolved below `.worktrees/v1.1-alarm-investigation-reliability/src` |
| E03 | Establish isolated implementation branch | CLOSED_VERIFIED | `codex/v1.1-alarm-investigation-reliability` at the starting HEAD |
| E04 | Run the unchanged baseline test suite | CLOSED_VERIFIED | `PYTHONPATH="$(pwd)/src" python3 -m pytest -q`: `132 passed` |
| E05 | Capture current CLI help, repository docs, protocol, and validation baseline | IN_PROGRESS | Exact evidence will be recorded in this run |
| E06 | Keep this checklist synchronized and close every row | IN_PROGRESS | Final self-audit required |

## Closure A - acquisition contract repair

| ID | Requirement | State | Evidence |
|---|---|---|---|
| A01 | Add conservative candidate `semantic_kind` without changing wire identity | IN_PROGRESS | Code, fixture, tests, docs, verification required |
| A02 | Resolve trace action type from semantic kind plus request type | IN_PROGRESS | Stable Web/BG rules retained; Dubbo composite remains unresolved absent Live proof |
| A03 | Gate `investigate_trace` on exact identity and the semantic resolver | IN_PROGRESS | CLI/runtime regression tests required |
| A04 | Normalize External Calls `text` to name and `value` to dependency URI with deterministic precedence | IN_PROGRESS | Raw shape and nonempty normalized rows required |
| A05 | Preserve recent response ranking value and wire-field provenance | IN_PROGRESS | `response` mapping and sort proof required |
| A06 | Preserve recent error ranking value and wire-field provenance | IN_PROGRESS | `error` mapping and sort proof required |
| A07 | Preserve recent throughput ranking value and misspelled `throught` provenance | IN_PROGRESS | normalized throughput metric plus wire field required |
| A08 | Classify thrown, logged-error, error-flag-false, and unknown exception signals conservatively | IN_PROGRESS | Candidate exception count remains uninterpreted wire metric |
| A09 | Adapt Core/Source Evidence Envelopes into at least three local depth primitives | IN_PROGRESS | run/artifact/evidence-path input; zero HTTP/Run/index mutation |
| A10 | Propagate only verified Candidate links/navigation through composition and readiness | IN_PROGRESS | No guessed URLs; acquisition-versus-compilation loss separated |
| A11 | Compare the alarm-events request contract offline and reach an evidence-backed terminal state | IN_PROGRESS | Method/path/body/paging/time/event/frequent/lang/scope comparison required |
| A12 | Compare the application-instances request contract offline and reach an evidence-backed terminal state | IN_PROGRESS | Item kind/scope/time/endpoint/body comparison required |

## Closure B - investigation selection reliability

| ID | Requirement | State | Evidence |
|---|---|---|---|
| B01 | Add local `tingyun inspect candidates match` CLI | IN_PROGRESS | Must emit schema/run/time/query/matches and perform zero HTTP/Run/index writes |
| B02 | Implement deterministic EXACT, STRONG, WEAK, and NOT_FOUND matching | IN_PROGRESS | No fuzzy similarity, embeddings, or LLM |
| B03 | Enforce match execution eligibility and preserve match basis | IN_PROGRESS | EXACT still uses available actions; WEAK never auto-executes |
| B04 | Implement shared trace target check | IN_PROGRESS | EXACT_TARGET/STRONG_TARGET/WRONG_TARGET/UNVERIFIABLE |
| B05 | Preserve wrong-target Trace for audit while rejecting it from Incident evidence | IN_PROGRESS | Lineage proof required |
| B06 | Add local `tingyun depth trace-sample-assess` CLI | IN_PROGRESS | Candidate plus Trace, optional alarm context; zero HTTP/Run |
| B07 | Compute deterministic duration position | IN_PROGRESS | P99/P95/P50 bands and unavailable state |
| B08 | Classify ABNORMAL_ALIGNED, NORMAL_CONTRAST, and UNKNOWN conservatively | IN_PROGRESS | Aggregate and Trace sample remain separate; no root-cause output |
| B09 | Add parent-transaction-first guidance for unresolved Dubbo/Interface candidates | IN_PROGRESS | Plan/docs only; no automatic execution |

## Closure C - deterministic evidence composition

| ID | Requirement | State | Evidence |
|---|---|---|---|
| C01 | Define and validate investigation manifest schema v1 | IN_PROGRESS | Unique seeds/incidents/windows/bindings; finite enums; explicit identities |
| C02 | Implement `tingyun depth evidence-compile` as local-only capability | IN_PROGRESS | Zero HTTP/Run/data-root/index/inflight mutation |
| C03 | Implement `tingyun depth evidence-validate` as local-only capability | IN_PROGRESS | PASS/FAIL and deterministic issues |
| C04 | Validate cross-window collect identity | IN_PROGRESS | `CROSS_WINDOW_EVIDENCE_REJECTED` |
| C05 | Validate exact `source_run_id + item_ref` identity | IN_PROGRESS | `ITEM_REF_NOT_FOUND` and missing artifact/run handling |
| C06 | Validate canonical incident references for every binding kind | IN_PROGRESS | `NONCANONICAL_INCIDENT_ID` |
| C07 | Validate trace target lineage independently of manifest assertions | IN_PROGRESS | `WRONG_TARGET_TRACE_REJECTED` |
| C08 | Validate Call Tree lineage and retain every target-correct tree | IN_PROGRESS | `BROKEN_CALL_TREE_LINEAGE` and closure proof |
| C09 | Validate canonical source bindings and roles | IN_PROGRESS | No name-based joins |
| C10 | Enforce empty/new output directory and atomic publication | IN_PROGRESS | `OUTPUT_DIR_NOT_EMPTY`; no silent overwrite or partial product |
| C11 | Emit deterministic `source-of-truth.json` | IN_PROGRESS | hashes, canonical registries, run refs, required counts; no current time |
| C12 | Emit nonempty `evidence-map.json` for evidenced Incidents | IN_PROGRESS | Alarm to raw evidence chain, links and gaps |
| C13 | Emit four-layer `coverage.json` | IN_PROGRESS | inventory/context/candidate/deep statuses from source of truth |
| C14 | Emit `validation.json` with ERROR/WARNING/INFO issues | IN_PROGRESS | ERROR makes compilation FAILED |
| C15 | Emit `report-readiness.json` for simple and deep report contracts | IN_PROGRESS | READY/PARTIAL/NOT_READY without report generation |
| C16 | Emit exact candidate extractions scoped to binding window | IN_PROGRESS | metrics, semantics, actions, verified links |
| C17 | Emit target-correct Trace extractions and shared sample assessment | IN_PROGRESS | timeline/topology/flows/errors/exceptions/links |
| C18 | Emit deep Call Tree extraction | IN_PROGRESS | root/downstream/DB/HTTP/Dubbo/Redis/exclusive leaves/errors/exceptions/logs |
| C19 | Preserve deep SQL and long HTTP spans with identity, parent, depth, timing, and evidence ref | IN_PROGRESS | exclusive-time ranking or total-time overlap warning |
| C20 | Emit external, recent-request, timeseries, and topology extractions where bound | IN_PROGRESS | Deterministic source-role routing |
| C21 | Prove byte-stable core outputs for identical manifest and Runs | IN_PROGRESS | Repeated SHA-256 equality; no time/random/temp paths |

## Sanitized corpus, fixtures, and offline replay

| ID | Requirement | State | Evidence |
|---|---|---|---|
| R01 | Inspect the private 7-day bundle locally and create a sanitized Live Evidence Case Register | IN_PROGRESS | No private payload is copied into Git |
| R02 | Register CASE-001 Web TX,IF to TX success | IN_PROGRESS | Structural evidence only |
| R03 | Register CASE-002 Dubbo TX,IF to TX failure | IN_PROGRESS | Structural evidence only |
| R04 | Register CASE-003 Dubbo IF in Call Tree | IN_PROGRESS | Structural evidence only |
| R05 | Register CASE-004 External text/value | IN_PROGRESS | Structural evidence only |
| R06 | Register CASE-005 response ranking raw metric | IN_PROGRESS | Structural evidence only |
| R07 | Register CASE-006 error ranking raw metric | IN_PROGRESS | Structural evidence only |
| R08 | Register CASE-007 throughput ranking raw metric | IN_PROGRESS | Structural evidence only |
| R09 | Register CASE-008 logged error with `error=false` | IN_PROGRESS | Structural evidence only |
| R10 | Register CASE-009 abnormal aggregate with normal Trace sample | IN_PROGRESS | Structural evidence only |
| R11 | Register CASE-010 cross-window same-name contamination | IN_PROGRESS | Structural evidence only |
| R12 | Register CASE-011 successful wrong-target Trace | IN_PROGRESS | Structural evidence only |
| R13 | Register CASE-012 canonical incident drift | IN_PROGRESS | Structural evidence only |
| R14 | Register CASE-013 deep SQL extraction loss | IN_PROGRESS | Structural evidence only |
| R15 | Create sanitized `candidate_web_tx_if.json` | IN_PROGRESS | Structure/equality/time relations retained |
| R16 | Create sanitized `candidate_dubbo_tx_if.json` | IN_PROGRESS | Structure/equality/time relations retained |
| R17 | Create sanitized `external_text_value.json` | IN_PROGRESS | Structure/equality/time relations retained |
| R18 | Create sanitized response/error/throughput ranking fixtures | IN_PROGRESS | Wire spelling and semantic uncertainty retained |
| R19 | Create sanitized `logged_error_false.json` | IN_PROGRESS | Error flag and message semantics retained |
| R20 | Create sanitized `aggregate_abnormal_trace_normal.json` | IN_PROGRESS | Aggregate/sample contrast retained |
| R21 | Create sanitized cross-window same-name fixture | IN_PROGRESS | Two windows and exact item identities retained |
| R22 | Create sanitized wrong-target Trace fixture | IN_PROGRESS | Wrong and replacement lineage retained |
| R23 | Create sanitized deep Call Tree fixture | IN_PROGRESS | Web to Dubbo to DB/SQL plus long HTTP branch retained |
| R24 | Build offline replay with 2 systems, 3 windows, 4 seeds, 3 incidents, 3 collects, wrong/correct Trace, Call Tree, External | IN_PROGRESS | End-to-end manifest and immutable synthetic Runs |
| R25 | Replay rejects cross-window, wrong-target, and noncanonical identities | IN_PROGRESS | Dedicated assertions and validation issues |
| R26 | Replay retains the correct Call Tree, deep spans, verified URL, and nonempty evidence map | IN_PROGRESS | Compiler/validator evidence |

## Test and integration matrix

| ID | Requirement | State | Evidence |
|---|---|---|---|
| T01 | Preserve all existing baseline tests | IN_PROGRESS | Final exact-checkout suite required |
| T02 | Candidate semantic and resolver tests | IN_PROGRESS | Web and unresolved Dubbo composite cases |
| T03 | Available-action eligibility tests | IN_PROGRESS | Unresolved action type hides Trace action |
| T04 | External normalization tests | IN_PROGRESS | Nonempty text/value mapping |
| T05 | Three recent ranking metric tests | IN_PROGRESS | response/error/throughput values and wire fields |
| T06 | Four exception classification tests | IN_PROGRESS | thrown/logged/error-false/unknown |
| T07 | Evidence Adapter tests for at least three depth primitives | IN_PROGRESS | Direct envelope consumption and no side effects |
| T08 | Candidate match level and CLI tests | IN_PROGRESS | Exact/strong/weak/not-found and local-only |
| T09 | Trace target and wrong-target audit/rejection tests | IN_PROGRESS | Exact lineage and evidence-map exclusion |
| T10 | Sample duration and three assessment-state tests | IN_PROGRESS | Shared CLI/compiler semantics |
| T11 | Cross-window and canonical Incident compiler tests | IN_PROGRESS | Hard failure codes |
| T12 | Call Tree lineage and deep SQL/HTTP preservation tests | IN_PROGRESS | Deep-node extraction proof |
| T13 | Verified URL propagation tests | IN_PROGRESS | Candidate, map, and readiness |
| T14 | Determinism SHA tests | IN_PROGRESS | Two compiles, byte equality |
| T15 | Compiler/validator atomicity and local-only tests | IN_PROGRESS | No HTTP/Run/data-root/index/inflight writes |
| T16 | CLI help and actual surface integration tests | IN_PROGRESS | Four new commands reachable |

## Re-audit of 35 Main Closure Contracts

| ID | Requirement | State | Evidence |
|---|---|---|---|
| M01 | Agent-first | IN_PROGRESS | Re-audit code/docs/tests |
| M02 | Immutable Runs | IN_PROGRESS | Re-audit code/docs/tests |
| M03 | Source pair identity | IN_PROGRESS | Re-audit code/docs/tests |
| M04 | Opaque item refs | IN_PROGRESS | Re-audit code/docs/tests |
| M05 | Exact time | IN_PROGRESS | Re-audit code/docs/tests |
| M06 | No time approximation | IN_PROGRESS | Re-audit code/docs/tests |
| M07 | FAILED versus EMPTY | IN_PROGRESS | Re-audit code/docs/tests |
| M08 | PARTIAL Run | IN_PROGRESS | Re-audit code/docs/tests |
| M09 | Dynamic Raw provenance | IN_PROGRESS | Re-audit code/docs/tests |
| M10 | One transient retry | IN_PROGRESS | Re-audit code/docs/tests |
| M11 | Retry only 502/503/504 | IN_PROGRESS | Re-audit code/docs/tests |
| M12 | Run-scoped auth recovery | IN_PROGRESS | Re-audit code/docs/tests |
| M13 | Serial Live execution | IN_PROGRESS | Re-audit code/docs/tests |
| M14 | Request pacing | IN_PROGRESS | Re-audit code/docs/tests |
| M15 | Strict action exposure | IN_PROGRESS | Re-audit code/docs/tests |
| M16 | Shared action-type resolver | IN_PROGRESS | Re-audit code/docs/tests |
| M17 | Trace/navigation separation | IN_PROGRESS | Re-audit code/docs/tests |
| M18 | Error rate remains percent | IN_PROGRESS | Re-audit code/docs/tests |
| M19 | Continuation uses current Run | IN_PROGRESS | Re-audit code/docs/tests |
| M20 | Stale inflight recovery | IN_PROGRESS | Re-audit code/docs/tests |
| M21 | Active inflight protection | IN_PROGRESS | Re-audit code/docs/tests |
| M22 | Plan-only zero effects | IN_PROGRESS | Re-audit code/docs/tests |
| M23 | Machine-safe invalid plan | IN_PROGRESS | Re-audit code/docs/tests |
| M24 | Missing-auth preflight | IN_PROGRESS | Re-audit code/docs/tests |
| M25 | Validation before lock | IN_PROGRESS | Re-audit code/docs/tests |
| M26 | Logical requests versus attempts | IN_PROGRESS | Re-audit code/docs/tests |
| M27 | Shared pseudonyms | IN_PROGRESS | Re-audit code/docs/tests |
| M28 | Array identities sanitized | IN_PROGRESS | Re-audit code/docs/tests |
| M29 | Composite identities sanitized | IN_PROGRESS | Re-audit code/docs/tests |
| M30 | Raw responses excluded | IN_PROGRESS | Re-audit code/docs/tests |
| M31 | Internal URLs removed from sanitized export | IN_PROGRESS | Re-audit code/docs/tests |
| M32 | Actions removed from sanitized export | IN_PROGRESS | Re-audit code/docs/tests |
| M33 | Exact fail-closed safety routing | IN_PROGRESS | Core/Advanced exact; WRITE/UNKNOWN/cross-surface blocked |
| M34 | Qualified Live-Validated wording | IN_PROGRESS | Re-audit docs |
| M35 | Old Runs remain immutable | IN_PROGRESS | No migration or overlay mutation |

## Protocol and documentation

| ID | Requirement | State | Evidence |
|---|---|---|---|
| D01 | Add v1.1 reliability requirements document | IN_PROGRESS | `docs/requirements/tingyun-cli-v1.1-alarm-driven-investigation-reliability.md` |
| D02 | Add investigation manifest document and schema | IN_PROGRESS | `docs/investigation-manifest.md` plus machine-readable schema |
| D03 | Add evidence composition contract | IN_PROGRESS | `docs/evidence-composition.md` |
| D04 | Add report readiness contract grounded in both Word examples | IN_PROGRESS | `docs/report-readiness-contract.md` |
| D05 | Add Trace sample assessment contract | IN_PROGRESS | `docs/trace-sample-assessment.md` |
| D06 | Update README with five layers and no report-generator claim | IN_PROGRESS | User-facing command surface |
| D07 | Update AGENT investigation sequence | IN_PROGRESS | Seed to exact window/candidate/Trace/assessment/tree/compile/validate |
| D08 | Update runtime, evidence-depth, investigation, and promotion docs | IN_PROGRESS | Exact local/live and proof states |
| D09 | Update protocol for candidate/resolver/composition/sample/exception/URL semantics | IN_PROGRESS | `research/protocol/` consistency required |
| D10 | Complete offline replay report | IN_PROGRESS | `validation-analysis/v1.1/02-offline-replay-results.md` |
| D11 | Complete focused Live report | IN_PROGRESS | `validation-analysis/v1.1/03-focused-live-micro-experiments.md` |
| D12 | Complete small investigation report | IN_PROGRESS | `validation-analysis/v1.1/04-small-real-investigation.md` |
| D13 | Complete Main Contract re-audit | IN_PROGRESS | `validation-analysis/v1.1/05-main-contract-reaudit.md` |
| D14 | Complete code/test/fixture/doc/evidence-linked closure matrix | IN_PROGRESS | `validation-analysis/v1.1/06-final-closure-matrix.md` |

## Focused Live and small real investigation

| ID | Requirement | State | Evidence |
|---|---|---|---|
| L01 | Verify Live prerequisites only after all offline gates pass | IN_PROGRESS | Tests/protocol/replay/contracts/credential scan |
| L02 | Run at most six serial business requests and audit attempts | IN_PROGRESS | Maximum in-flight one; no brute force |
| L03 | Micro-experiment: DubboProvider TX,IF direct action type | IN_PROGRESS | Run only with safe credentials and exact historical candidate |
| L04 | Micro-experiment: alarm-events corrected request | IN_PROGRESS | Run only if offline comparison proves a contract delta |
| L05 | Micro-experiment: application-instances corrected request | IN_PROGRESS | At most one request after proven contract delta |
| L06 | Micro-experiment: Verified URL propagation if required | IN_PROGRESS | Run only when existing evidence cannot close acquisition status |
| L07 | Feed every eligible Live result back into code/tests/protocol/docs | IN_PROGRESS | Repair loop or external proof |
| L08 | Execute one small real historical Alarm investigation when prerequisites exist | IN_PROGRESS | Full seed/window/collect/match/Trace/assessment/tree/compile/validate chain |

## Security, exact-checkout verification, and Git finish

| ID | Requirement | State | Evidence |
|---|---|---|---|
| F01 | Prove zero WRITE and zero UNKNOWN runtime endpoints | IN_PROGRESS | Static and test scans |
| F02 | Prove zero private Runs, names, IDs, IPs, URLs, SQL, credentials, or cookies committed | IN_PROGRESS | Tracked-file and staged-content scans |
| F03 | Run full exact-checkout pytest with explicit `PYTHONPATH` | IN_PROGRESS | Final command output and count |
| F04 | Run protocol consistency and compileall | IN_PROGRESS | Final command outputs |
| F05 | Run offline replay and compiler/validator exact-checkout checks | IN_PROGRESS | Final SHA and validation results |
| F06 | Run `git diff --check` and checklist terminal-state scan | IN_PROGRESS | Zero whitespace/checklist failures |
| F07 | Record final pwd/HEAD/status/branch/origin/import origins | IN_PROGRESS | Exact final checkout evidence |
| F08 | Commit focused implementation, tests, docs, and validation changes | IN_PROGRESS | Commit list required |
| F09 | Integrate the temporary branch into `main` after all gates pass | IN_PROGRESS | Fast-forward/merge evidence required |
| F10 | Push `origin/main` | IN_PROGRESS | Remote push evidence required |
| F11 | Verify local `main == origin/main` and clean final worktree | IN_PROGRESS | Final hashes and statuses |
