# Generated Research Overview

> Generated from the four canonical files in `research/protocol/`; do not edit by hand.

Health: **PASS**. Endpoints: **400**; variants: **442**; capabilities: **29**; workflows: **5**; gaps: **18**.

## Capability maturity and Runtime status

| Capability | Verification | Runtime | Workflows | Gaps |
|---|---|---|---:|---:|
| `analyze_transaction_errors` | VERIFIED | NOT_PROMOTED | 1 | 2 |
| `assess_trace_sample` | VERIFIED | NOT_PROMOTED | 1 | 0 |
| `compile_investigation_evidence` | VERIFIED | NOT_PROMOTED | 1 | 0 |
| `get_trace_agent_context` | PARTIALLY_VERIFIED | NOT_PROMOTED | 1 | 1 |
| `get_trace_call_tree` | VERIFIED | NOT_PROMOTED | 4 | 0 |
| `get_trace_detail` | VERIFIED | NOT_PROMOTED | 4 | 5 |
| `get_trace_stack` | VERIFIED | ADVANCED_READ_ONLY | 2 | 1 |
| `list_alarm_events` | VERIFIED | ADVANCED_READ_ONLY | 2 | 1 |
| `list_business_systems` | VERIFIED | NOT_PROMOTED | 1 | 1 |
| `list_component_operations` | PARTIALLY_VERIFIED | RESEARCH_ONLY | 1 | 1 |
| `list_external_calls` | VERIFIED | ADVANCED_READ_ONLY | 1 | 0 |
| `list_recent_requests` | VERIFIED | ADVANCED_READ_ONLY | 1 | 0 |
| `list_request_overview_candidates` | VERIFIED | NOT_PROMOTED | 2 | 0 |
| `list_service_interfaces` | PARTIALLY_VERIFIED | NOT_PROMOTED | 1 | 0 |
| `list_trace_exceptions` | VERIFIED | ADVANCED_READ_ONLY | 3 | 1 |
| `list_transactions` | PARTIALLY_VERIFIED | NOT_PROMOTED | 2 | 3 |
| `manage_alarm_rules` | VERIFIED | REJECTED | 0 | 1 |
| `manage_anomaly_detection_policy` | VERIFIED | NOT_PROMOTED | 0 | 1 |
| `manage_business_settings` | PARTIALLY_VERIFIED | NOT_PROMOTED | 0 | 1 |
| `match_investigation_candidate` | VERIFIED | NOT_PROMOTED | 1 | 0 |
| `normalize_candidate_semantics` | VERIFIED | NOT_PROMOTED | 1 | 1 |
| `read_alarm_event_detail` | VERIFIED | ADVANCED_READ_ONLY | 1 | 2 |
| `read_application_overview` | VERIFIED | ADVANCED_READ_ONLY | 1 | 2 |
| `read_business_topology` | VERIFIED | NOT_PROMOTED | 1 | 1 |
| `read_performance_timeseries` | VERIFIED | ADVANCED_READ_ONLY+CORE_LIVE_VALIDATED+RESEARCH_ONLY | 1 | 0 |
| `resolve_action_context` | PARTIALLY_VERIFIED | NOT_PROMOTED | 1 | 2 |
| `search_trace_candidates` | VERIFIED | NOT_PROMOTED | 1 | 1 |
| `search_trace_logs` | PARTIALLY_VERIFIED | NOT_PROMOTED | 2 | 0 |
| `validate_compiled_evidence` | VERIFIED | NOT_PROMOTED | 1 | 0 |

## Health issues

No health issues.

## Navigation

Use `research-index.json` for endpoint, workflow, gap, promotion, distribution, orphan, and source-hash detail. Use `research/tools/research_views.py diff` to compare two generated JSON views.
