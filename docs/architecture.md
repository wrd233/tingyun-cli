# Architecture

```text
User or Agent intent
  -> external agent reasoning
  -> ty-apm-cli safe execution
  -> Tingyun API
  -> JSON evidence
  -> external analysis or report
```

The CLI owns catalog lookup, read-only safety gates, auth, redaction, HTTP execution, snapshot persistence, and coverage/gap files. Interpretation remains outside the CLI.
