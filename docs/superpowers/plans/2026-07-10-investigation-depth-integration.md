# Investigation Depth Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Semantically migrate all valuable donor investigation depth onto current main while preserving every Golden Path closure contract and leaving only pushed `main` among the involved branches.

**Architecture:** Keep main's three-request Core Collect and shared runtime infrastructure. Add a fixed advanced source registry whose recipes execute one read-only request through the existing executor/store, plus pure local depth and plan modules with no transport or Run dependency.

**Tech Stack:** Python 3.9+, argparse, pytest, JSON-shaped protocol YAML, Git worktrees.

## Global Constraints

- Zero Live Tingyun requests and zero Tingyun writes.
- Do not merge or cherry-pick donor commit `95a8225` wholesale.
- Main semantics win on every conflict.
- Core Collect remains three logical requests.
- Every donor file and capability receives a final migration status.
- Finish in this task: verify, fast-forward main, push, delete donor locally/remotely, delete temporary branch.

---

### Task 1: Local investigation and trust primitives

**Files:** Create focused modules under `src/tingyun_cli/`; adapt donor tests under `tests/`.

**Interfaces:** Pure functions consume mappings/lists and produce schema-versioned dictionaries; they never consume `RunStore`, `Config`, or a transport.

- [ ] Add failing tests proving selection lineage, comparison source refs, local narrowing with zero request attempts, correction overlays, metric status, triage, and deterministic CLI output.
- [ ] Run focused tests and confirm failures are missing-module/behavior failures.
- [ ] Implement the smallest adapted local modules; preserve exact timestamps, scope, `source_run_id`, `item_ref`, and source refs.
- [ ] Run focused tests and the full main suite.
- [ ] Commit the local primitive slice.

### Task 2: Advanced read-only source runtime

**Files:** Create source registry/builders/normalizers; modify `commands.py`, `cli.py`, `safety.py`; add source tests.

**Interfaces:** `run_source_capability(...)->receipt` validates locally, creates one immutable SOURCE Run, and executes exactly one registry request through `HttpExecutor`.

- [ ] Add failing tests for each source recipe, exact READ allowlist, identity/time/auth-before-lock, provenance, `FAILED`/`EMPTY`, logical-vs-attempt counts, and unchanged Core Collect count.
- [ ] Confirm focused tests fail for missing source surface.
- [ ] Implement fixed source recipes and conservative normalizers using current main infrastructure.
- [ ] Run focused tests and all closure tests.
- [ ] Commit the advanced source slice.

### Task 3: Workflow plans, protocol, docs, and accounting

**Files:** Create workflow/local CLI tests; update README, AGENT, architecture/contract/artifact/safety/live/export docs and four protocol files; complete `validation-analysis/branch-integration/`.

**Interfaces:** Workflow plans return deterministic steps, integrated capability status, expected logical request count, budget, blockers, and execute nothing.

- [ ] Add failing tests proving five plan names, zero side effects, deterministic output, and no unavailable capability masquerading as executable.
- [ ] Implement plans and CLI dispatch, then make focused tests pass.
- [ ] Synchronize protocol/docs without claiming new sources are Live-Proven.
- [ ] Complete donor, source, contract, test, and closure matrices with no unresolved row.
- [ ] Commit documentation and accounting.

### Task 4: Offline closure and Git integration

**Files:** Final verification reports only.

**Interfaces:** Final main equals origin/main; donor and temporary branches are absent locally/remotely; worktree is clean.

- [ ] Run full pytest, protocol checker, compileall, diff check, fake/local smokes, leak scan, safety exactness, and live-root fingerprint comparison.
- [ ] Fast-forward local main to the verified integration branch and rerun the full verification set.
- [ ] Push main and verify local main equals origin/main.
- [ ] Delete donor remote then local, remove the integration worktree/branch, fetch prune, and verify final branch state.

