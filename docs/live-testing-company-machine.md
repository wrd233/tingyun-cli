# Live Testing On A Company Machine

Run only on a company-controlled machine with approved read-only credentials.

```bash
export TY_APM_BASE_URL="..."
export TY_APM_API_KEY="..."
export TY_APM_SECRET_KEY="..."

ty-apm auth test
ty-apm catalog audit-safety
ty-apm catalog filter --safety read
ty-apm api call application.3_1_1.application_app_list --param timePeriod=60
ty-apm snapshot collect --profile application-context --application-id 123 --since 60m --run-id live_app_123
```

Confirm that stdout is one JSON envelope and that artifacts do not contain credentials or bearer tokens.
