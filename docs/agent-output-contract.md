# Agent Output Contract

All stdout is a single JSON envelope.

Success shape:

```json
{
  "ok": true,
  "command": "api.call",
  "data": {},
  "meta": {
    "request_id": "req_xxx",
    "run_id": "run_xxx",
    "source_api": {
      "catalog_id": "business_system.2_1.application_business_list",
      "method": "POST",
      "path": "/server-api/application/business/list"
    },
    "raw_file": "artifacts/runs/run_xxx/calls/0001.response.raw.json",
    "request_file": "artifacts/runs/run_xxx/calls/0001.request.json"
  },
  "warnings": []
}
```

Error shape:

```json
{
  "ok": false,
  "command": "api.call",
  "error": {
    "type": "UnsupportedSafetyLevel",
    "message": "first version only executes safety=read endpoints",
    "retryable": false
  },
  "meta": {},
  "warnings": []
}
```

Agents should parse `ok`, then `data` or `error`. Human-readable tables are intentionally not produced in the first version.

