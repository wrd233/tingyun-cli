# Investigation Manifest v1

`investigation-manifest.json` is the explicit, user/Agent-authored binding
contract consumed by `tingyun depth evidence-compile`. The machine-readable
schema is [`schemas/investigation-manifest.schema.json`](../schemas/investigation-manifest.schema.json).
The compiler reads this committed Draft 2020-12 schema at runtime and enforces
its required fields, finite enums, types, uniqueness, and
`additionalProperties=false` rules before resolving any Run.

## Top-level shape

```json
{
  "schema_version": 1,
  "investigation_id": "investigation-001",
  "alarm_seeds": [],
  "incidents": [],
  "windows": [],
  "candidate_bindings": [],
  "trace_bindings": [],
  "call_tree_bindings": [],
  "source_bindings": []
}
```

All IDs are opaque strings. Names never act as join keys.

## Registries

`alarm_seeds` requires unique `alarm_seed_id`, `occurred_at`,
`business_system_name`, and `object_name`. An external Excel, monitoring
system, or human observation is valid; a Tingyun Run is not required.

`incidents` requires unique `incident_id`, an explicit `alarm_seed_ids` list,
and one finite kind: `TEMPORAL_INCIDENT`, `CALL_CHAIN_INCIDENT`,
`SERVICE_FAMILY_CLUSTER`, `RECURRING_ALARM_CLUSTER`, `INSTANCE_CLUSTER`, or
`OTHER`. The compiler validates this grouping; it does not create it.

`windows` requires unique `window_id`, `collect_run_id`, `incident_ids`, and
`alarm_seed_ids`. Actual time comes from the immutable Collect Run. Optional
`expected_time_context` is only an assertion against that source of truth.

## Bindings

Candidate binding required fields are `binding_id`, `alarm_seed_id`,
`incident_id`, `window_id`, `collect_run_id`, `item_ref`, and `match_level`.
`match_level` is `EXACT` or `STRONG`; `match_basis` is optional. The compiler
requires the binding Run to equal the Window's Collect Run and finds the item
by exact `source_run_id + item_ref`.

Trace binding fields are `incident_id`, `candidate_binding_id`,
`trace_run_id`, and declared `target_match` (`EXACT` or `STRONG`). The declared
match is not trusted: the compiler recomputes lineage from the Trace Run.

Call Tree binding fields are `incident_id`, `trace_run_id`, and
`call_tree_run_id`. Both Run manifest lineage and artifact source lineage must
point to the target-correct Trace.

Source binding fields are `incident_id`, `source_run_id`, and a finite `role`:
`external_calls`, `recent_requests_response`, `recent_requests_error`,
`recent_requests_throughput`, `performance_error_series`,
`performance_throughput_series`, `application_instances`, `trace_exceptions`,
`alarm_detail`, `alarm_metric_series`, or `other`. A role must match the Run's
artifact kind; recent-request roles must also match ranking provenance.

## Example

```bash
tingyun depth evidence-compile \
  --manifest /path/to/investigation-manifest.json \
  --output-dir /path/to/new-compiled-directory
```

The output directory must not exist or must be empty. Existing compiled
products are never overwritten.
