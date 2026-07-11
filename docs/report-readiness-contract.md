# Report Readiness Contract

The compiler does not generate a report. It assesses whether its evidence can
support either of the two observed report shapes: a concise seven-day alarm
brief and an application-owner deep analysis.

## Simple readiness

Per Incident, the minimum fields are:

- alarm inventory and distribution context;
- Incident summary;
- key Candidate metrics;
- a target-correct key Trace;
- verified navigation links;
- explicit evidence gaps.

The machine requirements include `alarm_inventory`, `alarm_distribution`,
`important_incident`, `incident_summary`, `candidate_metrics`, `key_trace`,
`important_upstream_downstream`, `verified_url`/`key_links`, and explicit
`evidence_gap_accounting`/`evidence_gaps`. Every boolean is derived from the
accepted Evidence Map or canonical registries; no section is marked present by
a constant.

## Deep readiness

Per Incident, the minimum fields are:

- Alarm Seed;
- exact historical Window;
- Candidate aggregate;
- target-correct Trace sample;
- deterministic sample assessment;
- Call Tree;
- deep leaf spans;
- SQL or external evidence;
- counter-signals such as a normal contrast sample or `error=false` log event;
- explicit unknowns and evidence-chain gaps.

The machine fields are `alarm_seed`, validated `historical_context`,
`candidate_aggregate`, `trace_sample`, `sample_assessment`, `call_tree`,
`deep_spans`, `sql_or_external`, `counter_signals`, `unknowns`, and an exact
`evidence_chain` backed by extraction/Raw references.

## Status

`READY` means every required evidence class is present. `PARTIAL` means at
least one is present but the contract has gaps. `NOT_READY` means none of the
required classes is available. Readiness never asserts correctness of prose,
root cause, remediation, or business interpretation.

Verified URL absence is reported as an evidence gap. The compiler distinguishes
acquisition absence from propagation failure: if a Candidate claims successful
verified navigation but no verified link reaches the compiled extraction,
validation emits `URL_PROPAGATION_FAILURE` and compilation fails.
