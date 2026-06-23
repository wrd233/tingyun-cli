# Application Context

`application-context` collects a bounded factual portrait for one application.

Required input:

```bash
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
