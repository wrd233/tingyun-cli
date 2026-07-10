# Safety

## Read-only Surface

Runtime 只允许已登记的 Stable Read Endpoint。未知路径和写路径会被阻断。

安全面分为 Core allowlist 与 Advanced Source allowlist。`responseList` 等高级路径不会通过 Core `assert_read_endpoint`；只有带正式 `ADVANCED_SOURCE` recipe 标记且精确出现在 source allowlist 时才能执行。WRITE/UNKNOWN、research-only 和 orphan path 不进入任一生产 allowlist。

Runtime surface 只接受精确 `CORE` 或 `ADVANCED_SOURCE`。任何显式 `WRITE`、`UNKNOWN` 或其他未知 surface 都会在写 Raw request 和调用 transport 之前阻断，不能回退成 Core。

不提供：

```text
endpoint execute
capability run
generic request
```

## Secret Handling

凭据从环境读取，不通过普通参数传入。Run、Raw、Evidence、stdout、`runs.jsonl` 和 sanitized export 都不得保存 Secret。

默认生产 transport 缺少 `TINGYUN_AUTHORIZATION` 时，Live command 在 HTTP 前阻断：

```text
BLOCKED / AUTH_NOT_CONFIGURED
live_request_count = 0
```

## Serial Execution

单 Run 内业务请求完全串行。默认 start-to-start 间隔为 2 秒。

## Live Lock

同一 data root 同时只允许一个 live command 访问服务端。冲突生成：

```text
BLOCKED / LIVE_EXECUTION_BUSY
```

且不访问 HTTP。

确定性本地校验先于 Live Lock。无效 source、item、action 或 time shape 不会被 lock 冲突掩盖。

Source capability 同样先验证 capability、source ref、exact identity、time 和 auth，再获取 Live Lock。每个 source invocation 固定一个逻辑请求，不自动分页、不跨 source fanout。

## Startup Recovery

CLI 启动时只扫描 `.inflight/`。active owner PID 仍存活时保持原样；确认 stale 的 inflight Run 冻结为 `INTERRUPTED`，只保留 raw summary 和安全 preflight intent，不访问 HTTP、不刷新 token、不重新归一化历史 Raw。

## Retry

瞬时网络故障最多重试一次。所有 attempts 都有 Raw 记录。

默认只重试：

```text
TimeoutError / ConnectionResetError / selected network OSError
HTTP 502 / 503 / 504
```

不重试 4xx、HTTP 500、业务错误、EMPTY、参数错误或安全阻断。

## Auth Recovery

每个 Live Run 最多一次 Auth Recovery，并重放同一个只读请求一次。不会改变请求参数或冻结时间。

Auth Recovery 与 transient retry 分开记录；后续请求如果再次认证失效，会形成 `FAILED` Artifact，而不是再次恢复。
