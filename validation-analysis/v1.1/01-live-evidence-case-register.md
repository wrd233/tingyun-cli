# v1.1 Live Evidence Case Register

## Handling contract

The attached private seven-day bundle was inspected only in a temporary local
directory. No private Run, business name, ID, IP, URL, SQL, Token,
Authorization, or Cookie is present in this repository. Fixtures use synthetic
values while preserving field names, equality, parent/child, ranking, and time
relationships.

| Case | Private structural observation | Sanitized evidence | Closure |
|---|---|---|---|
| CASE-001 | A Web `SpringController` Candidate labelled `TX,IF` succeeds when resolved to `TX` | `candidate_web_tx_if.json`; semantic/resolver tests | `CLOSED_VERIFIED` |
| CASE-002 | A `DubboProvider` Candidate labelled `TX,IF` fails when Web's `TX` rule is reused | `candidate_dubbo_tx_if.json`; unresolved-action zero-HTTP test | `CLOSED_VERIFIED` |
| CASE-003 | A Dubbo span can carry interface/IF semantics inside a target-correct Call Tree | `deep_call_tree/call_tree.json` preserves Web -> Dubbo -> DB/SQL | `CLOSED_VERIFIED` |
| CASE-004 | External rows carry visible label in `text` and dependency value in `value` | `external_text_value.json`; deterministic precedence test | `CLOSED_VERIFIED` |
| CASE-005 | Response ranking value is carried by wire field `response` | `recent_response_ranking.json`; wire provenance test | `CLOSED_VERIFIED` |
| CASE-006 | Error ranking value is carried by wire field `error` | `recent_error_ranking.json`; wire provenance test | `CLOSED_VERIFIED` |
| CASE-007 | Throughput ranking value uses wire spelling `throught` | `recent_throughput_ranking.json`; wire provenance test | `CLOSED_VERIFIED` |
| CASE-008 | A Logged Error Message can have `error=false` without a thrown exception | `logged_error_false.json`; four-state exception classification test | `CLOSED_VERIFIED` |
| CASE-009 | Abnormal Candidate aggregate and a normal-duration Trace sample coexist | `aggregate_abnormal_trace_normal.json`; `NORMAL_CONTRAST` test | `CLOSED_VERIFIED` |
| CASE-010 | The same Candidate name exists in different historical Windows with different metrics | `cross_window_same_name/window_a_candidates.json` and `window_b_candidates.json`; cross-window compiler failure test | `CLOSED_VERIFIED` |
| CASE-011 | HTTP-success Trace can belong to the wrong Candidate target | `wrong_target_trace/scenario.json`; wrong Trace is audited and excluded | `CLOSED_VERIFIED` |
| CASE-012 | Incident identifiers drifted between intermediate evidence products | noncanonical Incident mutation test and explicit registry contract | `CLOSED_VERIFIED` |
| CASE-013 | Shallow extraction omitted deep Oracle/PostgreSQL SQL and long HTTP nodes | `deep_call_tree/call_tree.json`; all six nodes, both SQL vendors, and long HTTP span preserved | `CLOSED_VERIFIED` |

## Private evidence summary used for fixture design

- 32 immutable Run manifests and 52 request/response attempts were inspected.
- The bundle contained both target-correct and wrong-target Trace outcomes.
- Deep Call Tree shape used `data.call_tree.treeNode` plus `nodeMap` and included
  nested database/SQL and long external HTTP evidence.
- Candidate names repeated across historical windows, so names could not be
  used as identity.
- No verified navigation URL survived the private final product; v1.1 therefore
  distinguishes acquisition absence from compiler propagation failure.
- Alarm inventory came from an external tabular source, proving that an Alarm
  Seed need not originate in a Tingyun Run.

These statements are aggregate/structural only and cannot reconstruct a
private payload.
