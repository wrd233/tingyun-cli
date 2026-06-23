# Live Testing

Live testing is manual only and must run on a company-controlled machine with approved Tingyun credentials.

```bash
export TY_APM_BASE_URL="..."
export TY_APM_API_KEY="..."
export TY_APM_SECRET_KEY="..."
# optional
export TY_APM_TOKEN_CACHE_PATH=".ty-apm-token-cache.json"

ty-apm auth test
ty-apm catalog audit-safety
ty-apm catalog list
ty-apm api call application.3_1_1.application_app_list --param timePeriod=60
ty-apm api call business_system.2_2_2.data_business_updatetopologyshoworhidden
ty-apm snapshot collect --profile application-context --application-id 123 --since 60m --run-id live_app_123
```

Expected checks:

- Every command writes one parseable JSON envelope to stdout.
- The guarded/write example returns `ok=false` with `SafetyBlocked`.
- Snapshot artifacts are created only for `snapshot collect`.
- Artifacts do not contain API keys, secret keys, bearer tokens, or access tokens.
- No pytest or CI job calls real Tingyun.
