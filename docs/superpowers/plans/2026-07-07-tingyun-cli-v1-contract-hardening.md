# Tingyun CLI v1 Contract Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the existing Tingyun CLI v1 runtime contracts for failure, retry, auth recovery, provenance, partial runs, interruption, and audit-safe exports without broadening the stable action surface.

**Architecture:** Keep the current filesystem-backed immutable Run model and add only small explicit runtime concepts: a request execution result, step-level artifact builders, status classification, stable-action identity checks, and verified-link construction for already evidenced routes. Preserve `investigate_trace` and `inspect_call_tree` as the only stable investigation actions.

**Tech Stack:** Python 3.9+, argparse, urllib, pathlib/json, pytest.

## Global Constraints

- Do not add SQL, database, stack, logs, NoSQL, MQ, a generic Endpoint Executor, a Capability Runner, a workflow engine, or new stable actions.
- `live_request_count` means actual persisted HTTP request attempts.
- Raw request records are written before HTTP; raw response/error records are written before normalization.
- `derived_from` must point to the final supporting raw response/error for each artifact.
- `EMPTY` only means a successful query returned no trustworthy domain data; transport/business failures are `FAILED`.
- Auth recovery is run-scoped and may happen at most once per live command run.
- Retry remains a single replay and is limited to transport transient exceptions plus HTTP 502/503/504.
- `available_actions` are emitted only when the action-specific exact wire identity is complete.
- Tests and validation for this pass must make zero real Tingyun requests.

---

### Task 1: Regression Tests For Runtime Contracts

**Files:**
- Modify: `tests/test_discover_retry_cli.py`
- Modify: `tests/test_safety_storage_export.py`
- Modify: `tests/test_candidates.py`
- Modify: `tests/test_workflow_contract.py`
- Create if useful: `tests/test_contract_hardening.py`

**Interfaces:**
- Consumes existing `run_collect`, `run_investigate`, `HttpExecutor`, `RunStore`, and candidate inspect helpers.
- Produces failing tests for `ExecutionResult`, partial collect, FAILED-vs-EMPTY, narrowed retry, run-scoped auth, dynamic provenance, strict action identity, trace richness, interrupted request count, blocked intent, verified links, and sanitized export.

- [x] **Step 1: Write failing tests**

Cover these exact behaviors:

```python
def test_collect_finalizes_partial_run_when_one_step_fails(tmp_path): ...
def test_http_500_is_failed_not_empty_and_not_retried(tmp_path): ...
def test_transient_retry_uses_final_response_in_derived_from(tmp_path): ...
def test_auth_recovery_is_run_scoped(tmp_path): ...
def test_candidate_actions_require_complete_trace_identity(): ...
def test_investigate_rechecks_malformed_action_identity_before_http(tmp_path): ...
def test_trace_evidence_exposes_verified_domains(tmp_path): ...
def test_stale_inflight_counts_persisted_request_records(tmp_path): ...
def test_blocked_runs_preserve_safe_requested_intent(tmp_path): ...
def test_verified_candidate_link_requires_complete_identity(): ...
def test_sanitized_export_removes_new_sensitive_fields(tmp_path): ...
```

- [x] **Step 2: Verify RED**

Run focused tests:

```bash
python3 -m pytest tests/test_contract_hardening.py tests/test_candidates.py tests/test_safety_storage_export.py -q
```

Expected: fails against the current happy-path implementation.

### Task 2: HTTP Execution Result And Step Provenance

**Files:**
- Modify: `src/tingyun_cli/http.py`
- Modify: `src/tingyun_cli/commands.py`

**Interfaces:**
- Produces `ExecutionResult` with `outcome`, `response`, `final_response_ref`, `final_error_ref`, `attempt_refs`, `attempt_count`, `transient_retried`, and `auth_recovered`.
- Updates artifact builders to consume execution results instead of hardcoded raw refs.

- [x] **Step 1: Implement `ExecutionResult`**

Add a frozen dataclass in `http.py` and return it from `HttpExecutor.execute`.

- [x] **Step 2: Narrow retry and make auth recovery run-scoped**

Keep exactly one transient retry for exceptions and 502/503/504. Allow one auth recovery per executor instance.

- [x] **Step 3: Build failed artifacts from final raw error/response**

Add small helpers in `commands.py` to classify execution results and produce `FAILED` artifacts without leaving `.inflight` stale.

- [x] **Step 4: Verify GREEN for execution/provenance tests**

Run:

```bash
python3 -m pytest tests/test_contract_hardening.py::test_transient_retry_uses_final_response_in_derived_from tests/test_contract_hardening.py::test_auth_recovery_is_run_scoped -q
```

### Task 3: Partial Runs And Identity-Gated Actions

**Files:**
- Modify: `src/tingyun_cli/commands.py`
- Modify: `src/tingyun_cli/candidates.py`

**Interfaces:**
- Produces collect runs that finalize as `PARTIAL` when independent steps fail.
- Produces `investigate_trace` only for complete `bizSystemId/applicationId/actionId/requestType` identity.
- Produces `inspect_call_tree` only for complete call-tree identity, including `actionGuid` and `traceId`.

- [x] **Step 1: Add explicit action eligibility helpers**

Use simple predicates such as `is_investigate_trace_eligible(item)` and `is_inspect_call_tree_eligible(item)`.

- [x] **Step 2: Recheck action identity before network**

`run_investigate` must return `BLOCKED` with zero live requests when an old malformed item lists an action but lacks required identity.

- [x] **Step 3: Verify GREEN for partial and identity tests**

Run:

```bash
python3 -m pytest tests/test_contract_hardening.py::test_collect_finalizes_partial_run_when_one_step_fails tests/test_contract_hardening.py::test_investigate_rechecks_malformed_action_identity_before_http tests/test_candidates.py -q
```

### Task 4: Trace, Metrics, Interruption, Blocked Intent, Links, And Export

**Files:**
- Modify: `src/tingyun_cli/commands.py`
- Modify: `src/tingyun_cli/candidates.py`
- Modify: `src/tingyun_cli/storage.py`

**Interfaces:**
- Produces richer trace evidence blocks using verified trace detail fields.
- Aligns candidate metrics with the protocol-backed request/response contract and rejects unavailable metrics deterministically.
- Freezes stale inflight runs with truthful raw request counts and safe preflight metadata.
- Adds minimal verified candidate detail links only for complete identity and sanitizes them from export.

- [x] **Step 1: Enrich trace artifact**

Expose `summary`, `timeline`, `trace_topology`, `service_flow`, `request_service_flow`, `exceptions`, `embedded_stack`, and `context` without inventing a universal trace model.

- [x] **Step 2: Harden local inspect metrics**

Raise a local `ValueError` when a supported metric is unavailable for every candidate row.

- [x] **Step 3: Preserve interrupted and blocked intent**

Count raw request files during stale freeze and include safe requested intent in blocked `preflight.json` and manifest.

- [x] **Step 4: Add verified links and sanitize new fields**

Derive only `/web/server/action/overview/{bizSystemId}/{applicationId}/{actionId}` for complete candidate identity with `DERIVED_FROM_VERIFIED_ROUTE`; remove executable links, identities, and secrets from sanitized export.

### Task 5: Docs, Verification, Commit, Push

**Files:**
- Modify: `README.md`
- Modify: `AGENT.md`
- Modify: `docs/architecture.md`
- Modify: `docs/cli-contract.md`
- Modify: `docs/artifacts.md`
- Modify: `docs/safety.md`
- Modify: `docs/live-testing.md`
- Modify: `docs/sanitized-export.md`

**Interfaces:**
- Historical plan note: this pass originally produced docs for `Runtime-contract-hardened` status before later Live validation; current status is maintained in README and validation-analysis reports.

- [x] **Step 1: Update docs**

Document partial runs, strict `FAILED`/`EMPTY`, dynamic raw provenance, run-scoped auth recovery, narrowed retry, identity-gated actions, trace evidence blocks, verified links, interrupted count, blocked intent, and sanitized export behavior.

- [x] **Step 2: Run final gates**

Run:

```bash
python3 -m pytest -q
python3 research/tools/check_protocol_consistency.py
python3 -m compileall -q src tests research/tools/check_protocol_consistency.py
git diff --check
```

Run one representative fake/local CLI smoke with no real Tingyun requests, and run a credential-pattern scan over tracked files.

- [x] **Step 3: Commit and push**

Use:

```bash
git add README.md AGENT.md docs src tests
git commit -m "fix: harden tingyun evidence runtime contracts"
git push origin main
```
