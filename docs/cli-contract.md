# CLI Contract

## Live Commands

Live 命令：

```text
discover
collect
investigate
```

只输出小型 JSON Receipt：

```json
{
  "schema_version": 1,
  "command": "collect",
  "status": "SUCCESS",
  "run_id": "run-...",
  "manifest_path": ".tingyun-runs/runs/run-.../manifest.json"
}
```

`SUCCESS`、`PARTIAL`、`BLOCKED` 都表示 CLI 成功产出可信 Receipt，进程退出码为 0。

`PARTIAL` 不表示诊断结论。它表示 Run 已 finalized，但至少一个 required Artifact 在执行后成为 `FAILED` 或 `BLOCKED`。Agent 应读取 `coverage.json` 和每个 Artifact 的 `status`。

## Discover

```bash
tingyun discover --query "name"
```

访问业务系统树，生成 `evidence/targets.json`。名称只用于发现和过滤，不会静默选择目标。

## Collect

```bash
tingyun collect --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
```

输入必须来自 Discovery Run 的 target item。Core Evidence 固定为 identity、topology、performance、candidates。

`topology`、`performance`、`candidates` 是独立 evidence-producing step。Preflight 成功后，任一步 request 失败会生成对应 `FAILED` Artifact，Run 整体为 `PARTIAL`；其他成功 Artifact 仍保留。

支持时间：

- `last_30m`
- `last_60m`
- `YYYY-MM-DDTHH:MM..YYYY-MM-DDTHH:MM`

不能精确表达的时间形状会生成 `BLOCKED / UNSUPPORTED_TIME_SHAPE`，且 `live_request_count = 0`。

## Investigate

```bash
tingyun investigate --source-run-id run-... --source-item-ref item-0001 --action investigate_trace
```

Action 必须 exact 出现在 Source Item 的 `available_actions` 中。

CLI 还会在发起 HTTP 前重新校验该 Action 的必要 wire identity：

- `investigate_trace`：`bizSystemId`、`applicationId`、`actionId`、`requestType`
- `inspect_call_tree`：`bizSystemId`、`applicationId`、`actionGuid`、`traceId`

校验失败生成 `BLOCKED / ACTION_IDENTITY_INCOMPLETE`，不访问服务端。

## Inspect

```bash
tingyun inspect candidates all --run-id run-...
tingyun inspect candidates top --run-id run-... --metric p99 --limit 10
tingyun inspect candidates filter --run-id run-... --metric error_rate --operator ">" --value 0.05
```

`inspect` 是纯本地 JSON 视图，不创建 Run。

`top/filter` 只接受稳定 metric。若当前 Candidate Dataset 的所有行都缺失该 metric，CLI 返回 `LOCAL_ERROR / UNAVAILABLE_METRIC` JSON，而不是对缺省值做误导性排序。
