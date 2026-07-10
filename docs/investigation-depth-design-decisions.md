# Investigation Depth Design Decisions

- Main closure semantics are authoritative over donor implementation details.
- Broad source depth belongs in an explicit advanced namespace, not the default Golden Path.
- A fixed source registry is safer than a generic capability or endpoint runner.
- Local plans describe request budgets and blockers but never execute, queue, schedule, or fan out.
- Raw remains first-class; normalizers lift only bounded verified fields.
- Trace selection is explicit because an arbitrary sample can be normal even when its aggregate is abnormal.
- `overview.max`, unverified units, and fixed-duration clusters remain qualified rather than converted into root-cause claims.
