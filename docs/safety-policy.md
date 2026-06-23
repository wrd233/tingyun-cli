# Safety Policy

v1 blocks all write, guarded, unknown, and unsupported endpoints before authentication and before HTTP execution.

Side-effect terms such as create, update, delete, save, bind, unbind, execute, cancel, change, sort, move, import, configure, enable, and disable are treated conservatively. If an endpoint looks risky, it is blocked even when the HTTP method is `POST` and even when the upstream UI might use it for convenience.

Allowed execution route:

```bash
ty-apm api call <catalog_id>
```

Forbidden routes include raw path calls, `http`, `curl`, `--allow-write`, confirmation prompts, plugins, workflow DSLs, and server bridges.
