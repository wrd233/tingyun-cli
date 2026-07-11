# Trace Sample Assessment

`tingyun depth trace-sample-assess` compares one Candidate aggregate with one
Trace sample without claiming a root cause. It is local-only: zero HTTP and
zero Run.

```bash
tingyun depth trace-sample-assess \
  --candidate /path/to/candidate-or-candidates.json \
  --candidate-item-ref item-0001 \
  --trace /path/to/trace.json \
  --alarm-metric response_time
```

The command accepts either a Candidate item or a Candidate Evidence Envelope.
The compiler calls the same assessment function for target-correct Trace
extractions.

## Duration position

When verified P50/P95/P99 values and a Trace duration exist, the result is one
of `AT_OR_ABOVE_P99`, `P95_TO_P99`, `P50_TO_P95`, or `AT_OR_BELOW_P50`.
Insufficient data produces `UNAVAILABLE`; no unit is guessed.

## Sample assessment

- `ABNORMAL_ALIGNED`: the sample is at/above the relevant abnormal aggregate
  band or carries aligned error evidence.
- `NORMAL_CONTRAST`: the sample is at/below P50 without aligned error evidence
  while the aggregate indicates an abnormal population.
- `UNKNOWN`: the aggregate/sample relationship cannot be established.

The output retains alarm metric context, Trace duration, Trace error signal,
exception signal types, and the Candidate exception-count semantic status.
`exception_count` does not become a thrown-exception claim. A normal Trace does
not invalidate an abnormal aggregate; it is retained as a counter-signal.
