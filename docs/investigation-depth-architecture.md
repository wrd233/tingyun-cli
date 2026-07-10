# Investigation Depth Architecture

The product has three intentionally unequal layers:

1. Core Agent Surface: `discover -> collect -> inspect candidates -> investigate_trace -> inspect_call_tree`; this is the Live-validated Golden Path.
2. Advanced Read-only Source Surface: explicit one-request SOURCE Runs for deeper facts. It is serial, identity-gated, bounded, and not automatically chained.
3. Local Investigation Surface: deterministic selection, narrowing, comparison, diff, triage, corrections, promotion views, and workflow plans with 0 HTTP and 0 Run.

All Live layers share one executor, auth/retry/pacing contract, safety system, and Run store. There is no second transport, storage model, Candidate model, auth system, or workflow engine. Core Collect remains three logical requests; deeper performance series are explicit source capabilities.
