# Tingyun CLI v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the v1 Agent-first, Evidence Package-first, read-only Tingyun APM investigation CLI in the current repository.

**Architecture:** Implement a small Python standard-library CLI around immutable filesystem Runs. Runtime commands create auditable Run packages; local commands read existing evidence without HTTP or Run creation.

**Tech Stack:** Python 3.9+, argparse, urllib, pathlib/json, pytest.

## Global Constraints

- Runtime exposes only `discover`, `collect`, `investigate`, `inspect`, `--plan-only`, and `sanitized-export`.
- No generic endpoint executor, capability runner, workflow engine, SQLite, queue, worker, plugin framework, target registry, candidate database, or query DSL.
- All live commands are read-only, serial, lock-protected, paced, retry-bounded, and evidence-recording.
- Candidate Dataset primary source is `POST /server-api/graph/query/overview?request_overview`.
- `row_count == 1000` must not be treated as `FULL`.
- Raw request records are written before HTTP; responses/errors are written before normalization.
- Secrets never enter Run artifacts, stdout, `runs.jsonl`, fixtures, or sanitized export.

---

### Task 1: Runtime Skeleton And Offline Contract Tests

**Files:**
- Create: `pyproject.toml`
- Create: `src/tingyun_cli/*`
- Create: `tests/test_candidates.py`
- Create: `tests/test_workflow_contract.py`
- Create: `tests/test_safety_storage_export.py`
- Create: `tests/test_discover_retry_cli.py`

**Interfaces:**
- Produces `RunStore`, `Config`, `run_discover`, `run_collect`, `run_investigate`, `plan_collect`, `export_sanitized_run`, and candidate inspect helpers.

- [x] Write failing tests for candidate normalization, inspect, collect, investigate, storage, safety, retry, auth recovery, discover, and receipt stdout.
- [x] Verify tests fail on missing package imports.
- [x] Implement the minimal runtime modules to pass the tests.
- [x] Run `python3 -m pytest -q`.

### Task 2: Protocol Backfill

**Files:**
- Modify: `research/protocol/endpoint-contracts.yaml`
- Modify: `research/protocol/workflows.yaml`
- Modify: `research/protocol/tingyun-capability-protocol.md`
- Modify: `research/protocol/gaps-and-conflicts.md`

**Interfaces:**
- Produces a protocol-level `request_overview` endpoint variant and runtime capability/recipe references.

- [x] Add `variant_metric_request_overview` to `/server-api/graph/query/overview`.
- [x] Add a candidate capability that uses this endpoint and records row fields, identity use, and 1000-row boundary.
- [x] Update the protocol overview to state the Candidate source gate is closed.
- [x] Remove Candidate-source ambiguity from gaps without erasing unrelated gaps.
- [x] Run `python3 research/tools/check_protocol_consistency.py`.

### Task 3: User And Agent Documentation

**Files:**
- Create: `README.md`
- Create: `AGENT.md`
- Create: `docs/architecture.md`
- Create: `docs/cli-contract.md`
- Create: `docs/artifacts.md`
- Create: `docs/safety.md`
- Create: `docs/live-testing.md`
- Create: `docs/sanitized-export.md`

**Interfaces:**
- Produces human and Agent operating contracts consistent with the runtime.

- [x] Document install, config, workflow, Run locations, and local inspect.
- [x] Document Agent source-resolution rules and `available_actions`.
- [x] Document artifacts, safety, live testing, and sanitized export.
- [x] Confirm docs do not describe report generation or generic endpoint execution.

### Task 4: Final Verification

**Files:**
- Modify as needed based on verification output.

**Interfaces:**
- Produces a verified working tree with no known secret leakage.

- [x] Run full offline tests.
- [x] Run protocol consistency checker.
- [x] Compile Python modules.
- [x] Search for forbidden placeholders and secret-bearing terms in new runtime/docs.
- [x] Confirm no live requests were made during implementation.
