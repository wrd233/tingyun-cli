# Agent Action Contract

Every normalized Evidence Item may expose three related fields:

- `available_actions`: compatibility list of exact executable action IDs.
- `action_contracts`: machine-readable contracts for available actions.
- `action_blockers`: machine-readable explanation for withheld high-value actions.

An available contract contains `action`, `surface`, `status=AVAILABLE`, `logical_request_budget`, an explicit `cli` command/action-or-capability mapping, and exact `input.source_run_id + input.source_item_ref`. Current surfaces are `CORE_LIVE` and `ADVANCED_READ_ONLY`; both create an immutable Run and persist Raw before normalized evidence. Local-only tools remain explicit CLI commands and do not masquerade as Live actions.

A blocker contains `reason_code` and `missing_identity_fields`. It is not an invitation to guess. Important blockers include:

- `ACTION_IDENTITY_INCOMPLETE`: the Evidence Item lacks required wire identity.
- `UNRESOLVED_TRACE_ACTION_TYPE`: the semantic kind/requestType pair has no direct verified resolver.
- `RANKING_LINEAGE_NOT_INHERITED`: error/throughput ranking cannot reuse response ranking Trace proof.
- `TRACE_CANDIDATE_REQUIRED`: an alarm transaction target does not supply Candidate requestType and cannot jump directly to Trace.
- `SOURCE_IDENTITY_INCOMPLETE`: an Advanced Source lacks its exact scoped input.

Exact `trace_tree_node` items expose `source_trace_exceptions` and `source_trace_stack`, each with budget 1. Both consume the same treeId/traceId/bizSystemId/queryTimestamp evidence and explicit time context. Plain Trace items do not expose these actions.

`available_actions` means “can execute within the declared contract,” not “recommended,” “safe to auto-run,” or “likely root cause.” No Action Contract performs branching, retries a workflow, selects a node, or schedules another Action.
