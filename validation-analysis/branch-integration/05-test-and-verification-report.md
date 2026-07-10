# Test and Verification Report

## Offline verification

| Check | Result |
|---|---|
| `python3 -m pytest -q` | PASS, 106 passed |
| `python3 research/tools/check_protocol_consistency.py` | PASS |
| `python3 -m compileall -q src tests research/tools/check_protocol_consistency.py` | PASS |
| `git diff --check` | PASS |
| local CLI / primitive / workflow smoke | PASS, 23 tests |
| fake source transport / safety exactness smoke | PASS, 16 tests |
| Golden Path closure / sanitized export smoke | PASS, 16 tests |
| credential-value scan | PASS |
| private evidence tracking check | PASS, no tracked private/live roots |
| donor unique-file accounting | PASS |
| wholesale merge check | PASS, no merge commits from main to integration head |

The suite includes current main tests, adapted accepted donor tests, and new integration regression tests. It covers Core Golden Path behavior; all 35 closure contracts; local zero-side-effect behavior; exact Advanced Source READ paths; identity/time/auth-before-lock; raw-before-normalized persistence; dynamic provenance; FAILED/EMPTY; SOURCE Run lineage; Core request-count stability; workflow plan determinism; and source-aware external export sanitation.

## Zero-Live proof

The original checkout's private/live roots were fingerprinted from file modification time, size, and relative path without reading or reporting business identities.

| Snapshot | File count | Fingerprint |
|---|---:|---|
| baseline | 5 | `fce901b0f1575b4b43d43df4d140f035625f6e79` |
| post-integration verification | 5 | `fce901b0f1575b4b43d43df4d140f035625f6e79` |

Result: 0 new Live Run, 0 new Raw request record, 0 browser/curl/token-refresh request, and no private evidence committed. All source execution tests used fake local transports.
