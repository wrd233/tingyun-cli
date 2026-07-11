# Investigation Guide

Start with the Core Golden Path. Read Manifest and Coverage before artifacts, and preserve successful siblings in PARTIAL Runs.

Use one Advanced Source recipe only when Core Evidence identifies the exact next question. Never type naked IDs when an Evidence Item is available. Treat source list completeness as bounded unless total coverage is explicit.

Use `depth narrow-window`, `select-trace`, `compare-windows`, `diff-call-trees`, `cluster-errors`, and `analyze-external` only on existing Evidence. Their output is local analysis, not a new fact acquisition or diagnosis.

Five workflow plans are available: `slow_transaction`, `external_dependency_timeout`, `instance_anomaly`, `transaction_error`, and `alarm_to_trace`. Plans do not execute. A `RESEARCH_ONLY` step is an honest optional gap, not an executable promise.

For an alarm-led investigation, bind the external Seed to an exact historical Window, run Core Collect, and use `inspect candidates match`. Execute only an EXACT/eligible identity; retain STRONG match basis for review, and never auto-execute WEAK. Verify the Trace target independently, then run `trace-sample-assess` before following a target-correct Trace to its Call Tree.

For an unresolved Dubbo/interface Candidate, start from a verified parent Web transaction and inspect its target-correct Trace/Call Tree. Do not translate `DubboProvider + TX,IF` into `TX` or `IF` without direct proof, and do not auto-execute the parent-first guidance.

After evidence acquisition, write an explicit Investigation Manifest and run `evidence-compile`, followed by `evidence-validate`. Treat compiler `FAILED` and validator `FAIL` as evidence-integrity outcomes to repair, not as partial reports. The compiler never performs same-name joins, generates an RCA, or chooses another Live request.
