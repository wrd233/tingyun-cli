# Final v1 Closure Gap Matrix

Allowed final states: `CLOSED`, `VERIFIED_NOT_APPLICABLE`, `EXPLICITLY_UNRESOLVED_WITH_EVIDENCE`.

Summary: 49 known rows; 49 `CLOSED`; 0 `VERIFIED_NOT_APPLICABLE`; 0 `EXPLICITLY_UNRESOLVED_WITH_EVIDENCE`.

| ID | Gap | Evidence before | Implementation or decision | Tests / local proof | Final state | Files changed |
|---|---|---|---|---|---|---|
| G01 | shared Trace actionType resolver | Duplicate split/membership handling existed | Added `resolve_verified_trace_action_type` exact map | `test_shared_trace_resolver_uses_exact_verified_mappings_only` | CLOSED | `src/tingyun_cli/candidates.py` |
| G02 | eligibility/request-builder resolver consistency | Eligibility and request body could disagree | Both paths use the same resolver | `test_candidate_trace_eligibility_and_execution_use_same_resolver` | CLOSED | `src/tingyun_cli/candidates.py`, `src/tingyun_cli/commands.py` |
| G03 | unknown composite requestType withholding | Generic split could accept unknown composites | Unknown composites return `None` and block | resolver and malformed-old-evidence tests | CLOSED | `src/tingyun_cli/candidates.py`, `src/tingyun_cli/commands.py` |
| G04 | Trace proof vs Navigation proof separation | Trace success could emit route URL | Route proof is separate from Trace eligibility | `test_trace_proof_does_not_create_unproven_navigation_urls` | CLOSED | `src/tingyun_cli/candidates.py` |
| G05 | BG unproven URL removal | BG had links after latest live-resolution commit | BG keeps trace action but no URL | route separation tests | CLOSED | `src/tingyun_cli/candidates.py`, docs |
| G06 | ambiguous TX,IF URL removal unless independently proven | TX,IF had links via split logic | TX,IF keeps trace action but no URL | route separation tests | CLOSED | `src/tingyun_cli/candidates.py`, docs |
| G07 | one shared pseudonym state per export | Sanitizer built state per file | Export builds one state and reuses it | `test_sanitized_export_uses_one_pseudonym_state...` | CLOSED | `src/tingyun_cli/commands.py` |
| G08 | known identity in arrays | Known IDs in arrays could remain | Pass-2 string replacement covers arrays | sanitized export test aliases | CLOSED | `src/tingyun_cli/commands.py` |
| G09 | known identity in composite strings | Composite strings could leak IDs | Known identity tokens replaced in strings | sanitized export composite aliases | CLOSED | `src/tingyun_cli/commands.py` |
| G10 | cross-file pseudonym consistency | Same identity/name could vary by file | Whole-export pseudonym state | manifest/evidence pseudonym equality assertion | CLOSED | `src/tingyun_cli/commands.py` |
| G11 | arbitrary Raw response exclusion from external export | Older export included Raw responses | Export excludes raw responses by default | sanitized export raw response absence | CLOSED | `src/tingyun_cli/commands.py`, docs |
| G12 | internal URL removal from external export | URL strings/links could remain | URL keys removed and `/web/` strings redacted | sanitized export leak test | CLOSED | `src/tingyun_cli/commands.py` |
| G13 | available_actions removal from external export | Executable actions could be copied | `available_actions` removed | sanitized export tests | CLOSED | `src/tingyun_cli/commands.py` |
| G14 | local reprocessing of real Topology Raw | Old evidence said `EMPTY` | Reprocessed archived Raw with current normalizer | local report: `SUCCESS`, 13 nodes / 38 edges | CLOSED | reports, docs/protocol |
| G15 | local reprocessing of real Performance Raw | Old evidence said `EMPTY` | Reprocessed archived Raw with current normalizer | local report: five 30-point series | CLOSED | reports, docs/protocol |
| G16 | startup stale `.inflight` recovery wiring | Store method existed but CLI did not call it | CLI calls `freeze_stale_inflight()` on startup | startup recovery test | CLOSED | `src/tingyun_cli/cli.py` |
| G17 | startup recovery active-vs-stale safety | Active PID protection needed proof | Existing PID check preserved | stale/active storage tests | CLOSED | tests, storage behavior |
| G18 | plan-only invalid source deterministic local result | Missing source could traceback | Plan returns local `BLOCKED / INVALID_SOURCE_REF` | plan-only invalid tests | CLOSED | `src/tingyun_cli/commands.py` |
| G19 | plan-only invalid time deterministic local result | Invalid time could traceback | Plan returns local `BLOCKED / UNSUPPORTED_TIME_SHAPE` | plan-only invalid tests | CLOSED | `src/tingyun_cli/commands.py` |
| G20 | plan-only zero Run / zero index / zero HTTP guarantee | Needed side-effect proof | Plan-only stays read-only/local | snapshot before/after test | CLOSED | tests, docs |
| G21 | missing auth preflight block | Default transport could send without auth | Default live commands block before HTTP | missing auth tests | CLOSED | `src/tingyun_cli/commands.py` |
| G22 | missing auth zero HTTP guarantee | Needed attempt proof | Blocked Run has `live_request_count=0` | missing auth manifest assertions | CLOSED | tests |
| G23 | fake/local transport test compatibility with auth preflight | Auth block could break offline tests | Auth block applies only default transport | fake transport compatibility test | CLOSED | `src/tingyun_cli/commands.py` |
| G24 | local validation before live-lock conflict | Lock could hide invalid input | Local validation runs before lock acquisition | lock ordering test | CLOSED | `src/tingyun_cli/commands.py` |
| G25 | expected request count naming/semantics | `expected_live_request_count` ambiguous | New `expected_logical_request_count`; actual attempts remain `live_request_count` | request count test | CLOSED | code/docs/tests |
| G26 | Candidate error_rate percent semantics | Docs/protocol had ratio examples | Runtime/protocol/docs use percent | candidate tests and stale search | CLOSED | candidates, docs, protocol |
| G27 | Candidate continuation source_run_id semantics | Could confuse Discovery vs Collect Run | Collect passes current Collect Run ID into candidates | `test_source_run_id_preserved` | CLOSED | `src/tingyun_cli/commands.py`, docs |
| G28 | exact available_actions identity semantics | Old/manual evidence could bypass | Execution rechecks identity and resolver | malformed old evidence test | CLOSED | code/tests |
| G29 | responseList production safety-surface review | responseList in runtime allowlist | Removed from production runtime allowlist | responseList blocked test | CLOSED | `src/tingyun_cli/safety.py`, protocol docs |
| G30 | protocol same-run Core Collect correction | Protocol lagged Raw correction | Added same-run Raw correction | protocol consistency PASS | CLOSED | protocol/reports |
| G31 | protocol Topology exact Wire shape | Needed exact keys/shape | Documented `nodeDataArray` / `linkeDataArray`, micro counts | local report and protocol update | CLOSED | protocol/reports |
| G32 | protocol Performance exact Wire shape | Needed exact series shape | Documented `overviews`, `series[]`, response/P50/P80/P95/P99 | local report and protocol update | CLOSED | protocol/reports |
| G33 | protocol Candidate -> Trace exact mappings | Generic split risk | Documented exact resolver map only | tests + protocol update | CLOSED | protocol/docs |
| G34 | protocol Trace -> Call Tree lineage | Needed exact lineage | Recorded actionGuid and traceId lineage | Golden Path report | CLOSED | protocol/reports |
| G35 | protocol Navigation gap separation | Route conflated with trace | Protocol/docs separate Navigation proof | route separation tests | CLOSED | docs/protocol |
| G36 | docs project status synchronization | Docs said Runtime Candidate | Updated status to Golden Path Live-Validated with limits | stale status scan clean | CLOSED | README/docs/requirements |
| G37 | docs error_rate examples synchronization | Examples used ratio value | Updated examples to percent value | stale `0.05` scan clean except negative/test context | CLOSED | docs |
| G38 | docs plan-only semantics synchronization | Plan-only error behavior underdocumented | Added machine-safe zero-side-effect contract | docs + tests | CLOSED | docs |
| G39 | docs auth preflight synchronization | Missing auth not documented | Added `AUTH_NOT_CONFIGURED` semantics | docs + tests | CLOSED | docs |
| G40 | first Live validation correction report | No committed correction report | Added correction report | report exists | CLOSED | `validation-analysis/first-live-validation-correction.md` |
| G41 | Golden Path Live validation report | No committed final Golden Path report | Added validation report | report exists | CLOSED | `validation-analysis/golden-path-live-validation-report.md` |
| G42 | final closure report | No committed closure report | Added closure report | report exists | CLOSED | `validation-analysis/golden-path-closure-report.md` |
| G43 | stale text search across repo | Known stale terms existed | Fixed stale status/ratio/split code; remaining hits are tests/history/protocol evidence | targeted `rg` scans | CLOSED | docs/protocol/tests |
| G44 | old immutable Runs remain untouched | Risk of editing archived Runs | Reprocessed in `/tmp` only | no repo raw/evidence edits; reports state immutability | CLOSED | reports only |
| G45 | 0 Live requests during this task | Required proof | Used fake transports/offline archives only | repo data root raw count before/after remains zero | CLOSED | reports |
| G46 | private evidence remains untracked | Private archives local-only | Extracted to `/tmp`, no archive/raw added | git status/ls-files audit | CLOSED | no private files |
| G47 | all tests and protocol checks pass | Baseline was 45 tests | Added closure tests; protocol checker passes | `57 passed`; checker `PASS` | CLOSED | tests/protocol |
| G48 | working tree clean | Required finish state | Final commit includes all tracked changes; no residue | final `git status --short` check | CLOSED | git state |
| G49 | commit(s) pushed | Required finish state | Final change set committed and pushed to intended branch | final push and `HEAD == origin/main` check | CLOSED | git remote state |
