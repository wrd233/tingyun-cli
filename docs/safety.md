# Safety

## Read-only Surface

Runtime 只允许已登记的 Stable Read Endpoint。未知路径和写路径会被阻断。

不提供：

```text
endpoint execute
capability run
generic request
```

## Secret Handling

凭据从环境读取，不通过普通参数传入。Run、Raw、Evidence、stdout、`runs.jsonl` 和 sanitized export 都不得保存 Secret。

## Serial Execution

单 Run 内业务请求完全串行。默认 start-to-start 间隔为 2 秒。

## Live Lock

同一 data root 同时只允许一个 live command 访问服务端。冲突生成：

```text
BLOCKED / LIVE_EXECUTION_BUSY
```

且不访问 HTTP。

## Retry

瞬时网络故障最多重试一次。所有 attempts 都有 Raw 记录。

不重试 4xx、业务错误、EMPTY、参数错误或安全阻断。

## Auth Recovery

运行期明确认证失效时最多恢复一次，并重放同一个只读请求一次。不会改变请求参数或冻结时间。
