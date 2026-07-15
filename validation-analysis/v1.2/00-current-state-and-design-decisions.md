# v1.2 Current State and Design Decisions

## Independent baseline judgment

Baseline `f25a434655d52eac9cb4278c0b45f0635eb6cd5f` was clean, matched `origin/main`, imported `tingyun_cli` and `tingyun_cli.http` from this checkout, and passed 198 tests before modification.

The strongest existing assets were immutable Run/Raw/Artifact contracts, exact Evidence Item lineage, bounded Advanced Source recipes, deterministic Evidence Composition, and extensive sanitized fixtures. The main maintenance weakness was not missing protocol depth: it was the 62,876-line Endpoint ledger plus repeated handwritten summaries and an unmapped naming seam between protocol Capability IDs and Runtime promotion rows.

## Decisions

1. Keep all four protocol files canonical. Generate a compact join instead of splitting or truncating observations.
2. Make generated Research health fail on summary drift, broken references, unmapped Runtime capabilities and unsafe promotions. Report orphans without treating preserved historical/supporting contracts as errors.
3. Promote only exact node Stack. The 2026-07-15 evidence proves a non-empty stackTraces response and the existing Call Tree Runtime already emits the complete `trace_tree_node` identity. The resulting recipe is one immutable SOURCE Run and one logical request.
4. Keep Trace Search research-only. Its list-driven protocol path is verified, but the Runtime does not yet have a safe Evidence seed contract or committed minimal fixture for bounded search filters. It also must not close the DubboProvider direct resolver gap.
5. Keep transaction error representative selection research-only. exceptionStatistics proves one exact Trace identity path, but generic error selection and “representative” choice are not sufficiently specified.
6. Keep `application-instances` qualified by the observed HTTP 500 contract. No empty/permission/cause claim is added.
7. Extend Evidence Items without breaking `available_actions`: add `action_contracts` and `action_blockers`, while keeping execution authorization exact and server-side revalidated.
8. Implement System Model as a deep local module over explicit Run refs. Reuse schema validation, Run/Artifact/Item/Raw refs and Call Tree extraction; do not introduce a database, second Run model, mutable current state or Workflow executor.
9. Distinguish `STABLE_OWNERSHIP_OBSERVATION` from `WINDOWED_RUNTIME_OBSERVATION`. Diff uses `NOT_OBSERVED_IN_AFTER_INPUTS`, never deletion.
10. Release as CLI v1.2 / package 1.2.0 because Research View, exact Stack and System Model are public capabilities; retain `schema_version: 1` and old Run compatibility.

## Complexity budget

Added three focused modules: Research convergence, Action Contract and System Model. Added one Advanced Source command and three local System Model commands. No SQLite, graph database, daemon, queue, LLM, generic endpoint runner, automatic Agent, workflow engine or new transport abstraction was introduced.
