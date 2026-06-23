# Catalog Spec

Catalog file: `catalog/tingyun-apm-api.catalog.json`

Each endpoint includes:

- `id`
- `domain`
- `title`
- `section`
- `page`
- `method`
- `path`
- `safety`
- `execution_supported`
- `request.params`
- `response.fields`
- `evidence`
- `hints`
- `confidence`
- `uncertainties`

Allowed safety values are `read`, `write`, `guarded`, and `unknown`. v1 executes only `read` entries with `execution_supported=true`.
