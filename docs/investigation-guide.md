# Investigation Guide

Start with the Core Golden Path. Read Manifest and Coverage before artifacts, and preserve successful siblings in PARTIAL Runs.

Use one Advanced Source recipe only when Core Evidence identifies the exact next question. Never type naked IDs when an Evidence Item is available. Treat source list completeness as bounded unless total coverage is explicit.

Use `depth narrow-window`, `select-trace`, `compare-windows`, `diff-call-trees`, `cluster-errors`, and `analyze-external` only on existing Evidence. Their output is local analysis, not a new fact acquisition or diagnosis.

Five workflow plans are available: `slow_transaction`, `external_dependency_timeout`, `instance_anomaly`, `transaction_error`, and `alarm_to_trace`. Plans do not execute. A `RESEARCH_ONLY` step is an honest optional gap, not an executable promise.
