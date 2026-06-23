# Safety Policy

v1 blocks all write, guarded, unknown, and unsupported endpoints.

Side-effect terms such as create, update, delete, save, bind, unbind, execute, cancel, change, sort, move, import, configure, enable, and disable are treated conservatively. If an endpoint looks risky, it is blocked even when the HTTP method is `POST` and even when the upstream UI might use it for convenience.

There is no `--allow-write`, confirmation prompt, raw HTTP command, plugin system, or server bridge.
