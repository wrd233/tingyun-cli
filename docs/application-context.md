# Application Context

`application-context` collects a bounded factual portrait for one application.

Required input:

```bash
ty-apm snapshot collect --profile application-context --application-id 123 --since 60m --plan-only
ty-apm snapshot collect --profile application-context --application-id 123 --since 60m --run-id app_123
```

Sections:

- `identity.json`
- `topology.json`
- `behavior_samples.json`
- `rules_and_config.json`

Each section includes evidence pointers to call artifacts. The profile does not diagnose, score, recommend, or generate a human report.

The manifest records `scope`, `time_range`, `limits`, and `catalog_ref`. Evidence pointers include `catalog_id`, `call_id`, `artifact_path`, `item_count`, and `collected_at`.

The default window is `--since 60m`; callers may provide `--from` and `--to`. The profile is fixed and sequential: it does not branch into dynamic investigation based on collected data.

`application-context` uses explicit section-to-catalog mappings in code. It never scans broad domains to pick arbitrary endpoints, and it never fills missing IDs with fake values such as `1` or an empty string. Required params are derived only from explicit input, application identity, safe time/page defaults, or clearly named catalog fields. If a required param cannot be derived safely, that step is skipped and `coverage.json` records `missing_required_param`.
