# Semantic Migration Matrix

| Donor file/module | Donor capability | Main equivalent/conflict | Final location | Promotion status | Final state |
|---|---|---|---|---|---|
| `src/tingyun_cli/budgeting.py` | request/reuse ledger | no equivalent; must not execute/schedule | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/compare.py` | window/instance/tree compare | add lineage and stable node identity | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/corrections.py` | supersede overlay | old Runs immutable | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/evidence.py` | scope/metric trust | URL proof superseded by main; statuses tightened | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/narrowing.py` | narrow/peak | local rows are not requests | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/promotion.py` | promotion matrix | donor Stable overclaim rejected | same focused module | PORTED_LOCAL_ONLY | rewritten |
| `src/tingyun_cli/selection.py` | trace candidates/selection | exact action resolver and lineage required | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/source_capabilities.py` | fixed request builders | formal source registry required | same focused module | PORTED_ADVANCED_READ_ONLY | adapted |
| `src/tingyun_cli/source_normalization.py` | source normalizers | conservative shapes/no guessed identity | same focused module | PORTED_ADVANCED_READ_ONLY | adapted |
| `src/tingyun_cli/triage.py` | triage/clustering/external signal | no root-cause claim | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/workflows.py` | five plans | only integrated capabilities may be executable | same focused module | PORTED_LOCAL_ONLY | adapted |
| `src/tingyun_cli/candidates.py` changes | recent ranking candidates/URLs | main percent, current Run lineage, exact action/nav split win | `candidates.py` + source normalizer | PORTED_ADVANCED_READ_ONLY | adapted |
| `src/tingyun_cli/cli.py` changes | `source` and `depth` namespaces | preserve stale-inflight startup recovery | `cli.py` | PORTED_ADVANCED_READ_ONLY | adapted |
| `src/tingyun_cli/commands.py` changes | source Runs; 5-request collect | source adapted; collect expansion rejected | `commands.py` | PORTED_ADVANCED_READ_ONLY | adapted |
| `src/tingyun_cli/safety.py` changes | broader allowlist | orphan/read and research paths rejected | `safety.py` | PORTED_ADVANCED_READ_ONLY | adapted |
| `tests/test_depth_cli.py` | local/source CLI | main closure assertions added | integration tests | PORTED_LOCAL_ONLY | adapted |
| `tests/test_evidence_trust_depth.py` | trust helpers | semantic statuses tightened | integration tests | PORTED_LOCAL_ONLY | adapted |
| `tests/test_investigation_depth_primitives.py` | local primitives | zero side effects and lineage added | integration tests | PORTED_LOCAL_ONLY | adapted |
| `tests/test_source_capabilities_depth.py` | builders/promotion/5-request collect | collect assertions rejected | integration tests | PORTED_ADVANCED_READ_ONLY | adapted |
| `tests/test_source_runtime_depth.py` | SOURCE Runs | main validation/auth/lock/provenance added | integration tests | PORTED_ADVANCED_READ_ONLY | adapted |
| `tests/test_workflows_depth.py` | plan shapes | unavailable-step truth added | integration tests | PORTED_LOCAL_ONLY | adapted |
| donor `test_contract_hardening.py` edits | 5-request collect | contradicts main closure | existing main tests | REJECTED_WITH_REASON | default inflation rejected |
| donor `test_workflow_contract.py` edits | expected count 5 | contradicts main closure | existing main tests | REJECTED_WITH_REASON | main count 3 retained |
| `docs/evidence-schema-depth.md` | trust/source schemas | useful with tightened statuses | same doc | PORTED_LOCAL_ONLY | rewritten |
| `docs/investigation-depth-architecture.md` | three-layer model | stale in-progress and 5-request claim | same doc | PORTED_LOCAL_ONLY | rewritten |
| `docs/investigation-depth-design-decisions.md` | design rationale | compatible after main authority note | same doc | PORTED_LOCAL_ONLY | adapted |
| `docs/investigation-guide.md` | investigation path | donor makes depth effectively default | same doc | PORTED_LOCAL_ONLY | adapted |
| `docs/live-testing-investigation-depth.md` | offline/live scope | future live checklist retained as gap only | same doc | PORTED_RESEARCH_ONLY | adapted |
| `docs/migration-compatibility.md` | compatibility | 5-request change rejected | same doc | PORTED_LOCAL_ONLY | rewritten |
| `docs/protocol-promotion-matrix.md` | source promotion story | universal Stable rejected | same doc | PORTED_RESEARCH_ONLY | rewritten |
| `docs/runtime-surface.md` | runtime inventory | source becomes Advanced, not Stable Core | same doc | PORTED_ADVANCED_READ_ONLY | rewritten |
| `README.md` donor edits | product story/commands | stale status and overclaim rejected | `README.md` | SUPERSEDED_BY_MAIN | re-authored |
| `AGENT.md` donor edits | operating guide | main Golden Path hierarchy retained | `AGENT.md` | SUPERSEDED_BY_MAIN | re-authored |
| `docs/architecture.md` donor edits | depth layer | main Live-Validated wording retained | same doc | SUPERSEDED_BY_MAIN | re-authored |
| `docs/artifacts.md` donor edits | source/multi-step evidence | 5-request collect text rejected | same doc | SUPERSEDED_BY_MAIN | re-authored |
| `docs/cli-contract.md` donor edits | source/depth contract | main machine-safe closure retained | same doc | SUPERSEDED_BY_MAIN | re-authored |
| `docs/live-testing.md` donor edits | validation sequence | main completed Live validation retained | same doc | SUPERSEDED_BY_MAIN | re-authored |

