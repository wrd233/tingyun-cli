# Final Integration Runtime Integrity Repair

## Problem Summary

The final integration needed a trustworthy checkout-level Runtime Backbone audit. The reported P0 split (`commands.py` requiring `ExecutionResult` while `http.py` returned a dict) was not present in final `main`: `ExecutionResult`, dynamic provenance, Run-scoped auth recovery, and 502/503/504-only retry all matched hardened `4ecf1a9` semantics. One real safety defect was present: every runtime surface except exact `ADVANCED_SOURCE` fell through to the Core validator.

## Root Cause

Advanced Source routing was added as a two-way `if advanced / else core` branch. That made explicit `WRITE`, `UNKNOWN`, or future unknown surface labels eligible for Core allowlist validation. Separately, the previous final report did not record import origin or execute all 11 Source recipes end-to-end, so it could not prove which checkout supplied the passing tests or expose the surface fallthrough.

## ExecutionResult Repair

No production repair was required. Final main already imports and returns `ExecutionResult` with `outcome`, `response`, final response/error refs, attempt refs/count, transient retry, auth recovery, and reason code. A final-checkout contract test now imports the type and asserts the exact fields.

## Retry Repair

No production repair was required. Retry remains limited to supported transport exceptions and HTTP 502/503/504. Final integrity tests explicitly prove 500 = 1 attempt and 502/503/504 = 2 attempts.

## Run-scoped Auth Recovery Repair

No production repair was required. `HttpExecutor.auth_recovered` is executor-instance state shared across all requests in one Run. A new test proves request A may recover once and request B cannot recover again.

## Advanced Source Safety Routing

`HttpExecutor.execute()` now dispatches exact `CORE` to the Core validator, exact `ADVANCED_SOURCE` to the source validator, and rejects every other surface before Raw persistence or transport. Tests cover Core allowed, Advanced allowed, advanced-as-Core blocked, Core-as-Advanced blocked, and WRITE/UNKNOWN blocked.

## Advanced Source Runtime Verification

A parameterized fake-runtime test executes all 11 recipes through request construction, `HttpExecutor`, safety routing, Raw persistence, SOURCE Run finalization, normalized Evidence, Coverage, and Manifest. It covers performance error/throughput; alarm list/detail/metric; recent request response/error/throughput; application instances; external calls; and trace exceptions.

## Main Contract Re-audit

All 35 rows were re-audited. C33 was repaired and re-marked. The other 34 remain closed with explicit tests for FAILED/EMPTY/PARTIAL, dynamic provenance, retry/auth, serial/pacing behavior, strict actions/resolver/navigation separation, percent error rate, current-Run lineage, inflight recovery, plan-only, auth/lock ordering, request counts, sanitized export, and old-Run immutability.

## Test Import Origin

Bare `python3` does not import the package in this checkout, so final validation must not rely on an editable install. All pytest commands use `PYTHONPATH="$(pwd)/src"`. The validation preflight prints and asserts that both `tingyun_cli.__file__` and `tingyun_cli.http.__file__` are below the current checkout's `src` directory.

## Verification Results

Pre-commit repair verification: 132 tests passed, including 26 final-runtime integrity cases. Protocol consistency, compileall, diff check, credential scan, private evidence scan, Core fake smoke, and Advanced Source fake smoke are required again after the final commit; their final command outputs are recorded in the task response.

## Remaining Gaps

No offline Runtime Backbone blocker remains. Live use still requires real base URL/auth configuration and capability-specific Live evidence; this task intentionally made zero Live Tingyun requests and does not upgrade Advanced Source capabilities to collectively Live-Proven.
