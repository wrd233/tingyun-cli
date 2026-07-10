# Artifacts

## Run Layout

```text
run-.../
├── manifest.json
├── preflight.json
├── coverage.json
├── raw/
└── evidence/
```

## manifest.json

Manifest 是控制面和 Artifact Index。它记录 Run 类型、来源、时间、整体状态、Artifact 列表、Coverage 路径和请求数。

Manifest 不包含业务诊断摘要、推荐、根因或报告内容。

`live_request_count` 表示该 Run 实际持久化的 raw request attempt 数。一次 transient retry 或 auth replay 都算新的 attempt。Preflight 中的 `expected_logical_request_count` 表示计划逻辑请求数，不能与 actual attempts 混用。

`INTERRUPTED` Run 冻结时会保留 `raw_summary`，并在 preflight 已存在时带出安全的 `source`、`action` 和 `time_context`。

## preflight.json

Preflight 是当前一次 live command 的冻结执行边界。第一条真实请求前写入，执行开始后不再修改。新 Run 使用 `expected_logical_request_count`；旧 Run 中的 `expected_live_request_count` 只作为历史字段读取，不改写。

## coverage.json

Coverage 解释每个 Artifact 的状态和直接证据步骤。它不是 HTTP 日志，也不是第二份 Manifest。

状态：

```text
SUCCESS
EMPTY
FAILED
BLOCKED
SKIPPED
```

`FAILED` 和 `EMPTY` 严格分离：HTTP 4xx/5xx、传输异常、认证失败、业务失败都不能归为 `EMPTY`。成功响应中没有可信域数据才是 `EMPTY`。

Coverage step 会记录 `attempt_count`、`attempt_refs`、`transient_retried`、`auth_recovered` 和最终证据引用，便于审计 retry/auth replay 后的真实来源。

## raw/

Raw 保存非敏感请求意图和响应/错误。请求记录在 HTTP 前写入，响应/错误在返回后立即写入，然后才做 Normalization。

永不保存 Authorization、Cookie、Token、Password 或 Secret。

Normalized Artifact 的 `derived_from` 指向最终支撑该 Artifact 的 raw response 或 raw error。retry/auth replay 成功时，`derived_from` 指向最终成功 response，不指向早先失败 attempt。

## evidence/

Evidence 是 Agent 默认消费层。当前核心：

```text
targets.json
identity.json
topology.json
performance.json
candidates.json
trace.json
call_tree.json
alarm_events.json / alarm_detail.json / alarm_metric_series.json
performance_error_series.json / performance_throughput_series.json
recent_requests.json / instance_context.json / external_calls.json / trace_exceptions.json
```

Candidate 主来源是 `POST /server-api/graph/query/overview?request_overview`。`candidates.json` 保留实际获得的全部行，不做二次 Top N 裁剪。

Candidate `source_run_id` 属于创建它的 Collect Run。Agent 可直接复制 `inspect` 输出中的 `source_run_id + item_ref` 进入 `investigate`，不需要替换为父 Discovery Run。

`trace.json` 会提升 Trace Detail 中已验证的主要域：summary、timeline、trace-local topology、service flow、request service flow、embedded exceptions、embedded stack evidence 和 context。embedded stack 只表示 Trace Detail 内嵌证据，不关闭独立 `stackTraces` endpoint gap。

SOURCE Evidence Item 的 `source_run_id` 指向创建该 Item 的当前 SOURCE Run；父链保存在 Manifest `source` 和 Artifact `source.continuation_from`。Source payload 的完整上游响应只保存在 `raw/response-*.json`，Normalized Evidence 只提升保守字段并用 `source_refs` / `derived_from` 指向 Raw。

Source list completeness 只在可证明 total 已覆盖时为 `FULL`；其余使用 `BOUNDED` 或 `UNKNOWN`，不自动翻页。
