# Donor Capability Inventory

## Runtime modules

| Module | Capabilities reviewed | Main conflict |
|---|---|---|
| `budgeting.py` | bounded request/reuse ledger | must remain local metadata, not scheduler |
| `compare.py` | windows, instances, call-tree diff | donor drops source lineage and collides duplicate names |
| `corrections.py` | immutable supersede overlay | acceptable local-only concept |
| `evidence.py` | scopes, metric semantics, URL evidence | donor `PARTIAL` status and URL proof conflict with main |
| `narrowing.py` | narrow window, locate peak | donor counts local rows as live requests |
| `promotion.py` | promotion matrix | donor over-promotes all sources to Stable |
| `selection.py` | trace candidates and deterministic selection | donor guesses duration units and overexposes call-tree action |
| `source_capabilities.py` | 10 fixed source request variants | must use formal registry and main safety/runtime semantics |
| `source_normalization.py` | alarm, recent, instance, external, exception shapes | raw-in-normalized and heuristic claims require tightening |
| `triage.py` | path triage, error clusters, external candidate signal | local-only; no root-cause claim |
| `workflows.py` | five bounded plans | donor names unavailable primitives as executable |

## Changed main files

`candidates.py`, `cli.py`, `commands.py`, and `safety.py` contain valuable source/CLI ideas mixed with rejected Core Collect expansion and pre-closure semantics. `README.md`, `AGENT.md`, `docs/architecture.md`, `docs/artifacts.md`, `docs/cli-contract.md`, and `docs/live-testing.md` contain useful breadth but stale status and overclaims.

## Donor-only docs and tests

All eight donor-only docs and six donor-only test files are individually represented in the semantic migration matrix. Tests that encode five-request Core Collect or universal Stable promotion are rejected; accepted tests are rewritten against main contracts.

