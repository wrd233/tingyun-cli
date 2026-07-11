# v1.1 Offline Replay Results

## Scenario

The committed sanitized replay contains two business systems, three exact
historical Windows, four Alarm Seeds, three Incidents, three Collect Runs, one
same-name cross-window Candidate, one wrong-target Trace, one correct
replacement Trace, one target-correct Call Tree, and one External Source Run.

Input fixture:

```text
tests/fixtures/v1_1/offline_replay/
```

## Exact command result

Both compiles used `PYTHONPATH="$(pwd)/src" python3 -m tingyun_cli` and fresh
output directories. Results:

| Check | Result |
|---|---|
| Compiler status | `SUCCESS` |
| Compiler actual request count | `0` |
| Validator status | `PASS` |
| Validator issues | `[]` |
| Manifest hash | `17a386a95e08fe87f26da22919174974228efa0e6b1d9a128fdbe434126049e5` |
| First compiled tree hash | `6dd46b480c78a4d239916dacd22dd93063871f38f20f369a5091275df5104a74` |
| Second compiled tree hash | `6dd46b480c78a4d239916dacd22dd93063871f38f20f369a5091275df5104a74` |
| Input data-root content hash before/after | `cccbe819bab654ea7104888570be2e34b5800fd3ec02145e0cba5d02cb092548` |
| `.inflight` / `runs.jsonl` created | none |

## Source of truth counts

```json
{
  "alarm_seed_count": 4,
  "incident_count": 3,
  "window_count": 3,
  "collect_run_count": 3,
  "trace_run_count": 2,
  "target_correct_trace_count": 1,
  "call_tree_run_count": 1,
  "target_correct_call_tree_count": 1,
  "source_run_count": 1
}
```

All three Incidents have nonempty Evidence Maps. `run-trace-wrong` is retained
under `rejected_trace_runs` and absent from Incident trace chains. The correct
Trace and Call Tree are present in `incident-001`.

## Hard assertions

| Assertion | Evidence | State |
|---|---|---|
| No cross-window join | mutation to another Collect Run emits `CROSS_WINDOW_EVIDENCE_REJECTED`; no same-name substitution | `CLOSED_VERIFIED` |
| Exact item identity | missing item, Run, artifact, and Raw ref have explicit ERROR codes | `CLOSED_VERIFIED` |
| Canonical Incident | Candidate, Trace, Call Tree, and Source lineage mutations fail | `CLOSED_VERIFIED` |
| Wrong Trace rejection | wrong Run remains auditable and is absent from Evidence Map | `CLOSED_VERIFIED` |
| Call Tree closure | every target-correct bound tree is retained, including a two-tree regression | `CLOSED_VERIFIED` |
| Deep span preservation | six nodes retained; PostgreSQL and Oracle nodes keep SQL and `node-http` keeps `129397ms` total time | `CLOSED_VERIFIED` |
| Single source of truth | canonical registries/counts live in `source-of-truth.json`; validator checks count consistency | `CLOSED_VERIFIED` |
| Nonempty Evidence Map | every evidenced Incident has Candidate/Trace/Tree/Source references | `CLOSED_VERIFIED` |
| URL propagation | verified synthetic route reaches Candidate extraction, Evidence Map, and readiness; guessed proof fails compilation | `CLOSED_VERIFIED` |
| Source routing | External, Recent, Timeseries, and Topology bound roles route to exact extraction directories | `CLOSED_VERIFIED` |
| Trace artifact lineage | Manifest and artifact item both match exact Candidate source pair | `CLOSED_VERIFIED` |
| Artifact usability | FAILED/EMPTY Trace and Call Tree artifacts never become Incident evidence | `CLOSED_VERIFIED` |
| Formal Schema runtime | committed Schema rejects extra fields, wrong types, and invalid nested enums | `CLOSED_VERIFIED` |
| Context truthfulness | missing/invalid Collect context reports REJECTED, never SUCCESS | `CLOSED_VERIFIED` |
| Readiness truthfulness | every simple/deep report class is derived from accepted evidence | `CLOSED_VERIFIED` |

Malformed manifests publish deterministic failed validation products instead of
crashing. Nonempty output directories are rejected without overwriting their
contents. All publication is staged and atomically renamed.
