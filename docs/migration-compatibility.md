# Migration and Compatibility

Core commands, three-request Collect, immutable Run layout, exact action resolver, FAILED/EMPTY/PARTIAL semantics, and sanitized export remain compatible. Old Runs are not rewritten and readers tolerate absent depth/source fields.

New SOURCE Runs use `schema_version: 1`, `run_type: SOURCE`, the existing Manifest/Coverage/Raw/Evidence layout, `expected_logical_request_count: 1`, and actual attempt counting in `live_request_count`.

Donor's five-request Core Collect and universal Stable promotion were intentionally rejected. Error and throughput series are explicit source commands instead.
