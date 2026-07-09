# Local Reprocessing Report

Scope: offline reprocessing only. No live Tingyun requests were made. Private archives were extracted under `/tmp/tingyun-final-closure-*`, outside the repository, and old Run directories were not modified.

## Sources Used

- `/Users/wangrundong/Downloads/tingyun-live-validation 2.zip`
- `/Users/wangrundong/Downloads/20260707-0400-micro-shape-scope-validation.zip`

Only safe aggregate counts are recorded here. Real names, IDs, URLs, request bodies, and raw payloads are intentionally omitted.

## First Golden Path Raw Reprocessing

Archived collect Run: `run-20260707T154400-142370000`

| Artifact | Historical normalized status | Current local reprocessing status | Safe aggregate proof | Derived from |
|---|---:|---:|---|---|
| topology | `EMPTY` | `SUCCESS` | 13 structural nodes, 38 runtime edges | `raw/response-0001.json` |
| performance | `EMPTY` | `SUCCESS` | overview present; response_avg, P50, P80, P95, P99 each have 30 points | `raw/response-0002.json` |

Correction: the archived Raw responses were non-empty. The old `EMPTY` conclusion was caused by normalizers that did not read the live wire shapes now supported by the runtime.

## Micro Shape Scope Confirmation

Archive: `20260707-0400-micro-shape-scope-validation.zip`

| Endpoint | Confirmed request shape | Current local reprocessing status | Safe aggregate proof |
|---|---|---:|---|
| `/server-api/graph/queryBizDetailGraph` | `mergeGraph="1"`, `cascadingDisplay="1"` | `SUCCESS` | 12 structural nodes, 27 runtime edges |
| `/server-api/application/charts/response` | `businessType="BIZ_SYSTEM"` | `SUCCESS` | overview present; response_avg, P50, P80, P95, P99 each have 30 points |

The micro-run confirms exact executable shapes for protocol documentation. It does not prove that any single field is the sole cause of earlier failures and does not generalize to omitted `businessType` or other scopes.

## Immutability

No historical Run, preflight, manifest, evidence, or raw file was edited. Reprocessing was performed by loading archived Raw response files into the current normalizers in memory.
