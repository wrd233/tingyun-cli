# Catalog Spec

The catalog source of truth is `catalog/tingyun-apm-api.catalog.json`; its schema is `catalog/tingyun-apm-api.catalog.schema.json`.

Each endpoint contains:

- `id`: stable command/catalog identifier
- `title`, `domain`, `capability`
- `method`, `path`
- `description`
- `safety`: `read`, `guarded`, `write`, or `unknown`
- `execution_supported`: true only for `read`
- `request`: content type, parsed params, JSON schema, raw extracted table lines
- `response`: parsed fields, JSON schema, raw extracted table lines
- `examples`: short request/response PDF excerpts
- `doc`: PDF path, version, section, page range, text line range, short evidence
- `confidence`: `high`, `medium`, or `low`
- `uncertainties`
- `test`: priority, reasons, status
- `hints`: related ids and next-step hints

Duplicate paths are intentionally retained when the PDF presents the same path in different chapters or business contexts.

Regenerate with:

```bash
uv run python scripts/generate_catalog.py
```

