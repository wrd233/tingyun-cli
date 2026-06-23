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
