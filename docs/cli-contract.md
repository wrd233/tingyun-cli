# CLI Contract

## Live Commands

Live 命令：

```text
discover
collect
source
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

`action_contracts` 是同一可执行面的 machine-readable 扩展，声明 surface、精确输入和逻辑请求预算；`action_blockers` 解释 withheld Action。它们不改变旧 `available_actions` 的执行校验，也不会自动执行 Action。

CLI 还会在发起 HTTP 前重新校验该 Action 的必要 wire identity：

- `investigate_trace`：`bizSystemId`、`applicationId`、`actionId`、`requestType`
- `inspect_call_tree`：`bizSystemId`、`applicationId`、`actionGuid`、`traceId`

校验失败生成 `BLOCKED / ACTION_IDENTITY_INCOMPLETE`，不访问服务端。

## Inspect

```bash
tingyun inspect candidates all --run-id run-...
tingyun inspect candidates top --run-id run-... --metric p99 --limit 10
tingyun inspect candidates filter --run-id run-... --metric error_rate --operator ">" --value 5
```

`inspect` 是纯本地 JSON 视图，不创建 Run。

`top/filter` 只接受稳定 metric。若当前 Candidate Dataset 的所有行都缺失该 metric，CLI 返回 `LOCAL_ERROR / UNAVAILABLE_METRIC` JSON，而不是对缺省值做误导性排序。

`error_rate` 的稳定单位是 percent。筛选 5% 使用 `--value 5`，不是旧的 ratio-style 小数值。

## Advanced Source

`source` 子命令见 README。除 `alarm-events` 外都要求 `source_run_id + source_item_ref`；身份、时间、capability、auth 全部在 Live Lock 前校验。每次 recipe 的 `expected_logical_request_count = 1`，Manifest `live_request_count` 记录 retry/auth replay 后的实际 attempts。

SOURCE Run 使用现有目录布局和状态语义。response ranking 可在完整、精确、已验证 identity 下暴露 `investigate_trace`；error/throughput ranking 不继承 responseList 的 Trace lineage。`trace-exceptions` 与 `trace-stack` 只接受 exact `trace_tree_node`，各执行一个逻辑请求；普通 Trace 和自动 fan-out 都会在 HTTP 前阻塞。

## Local Depth and Workflow Plans

`depth` 命令只读输入 JSON并输出确定性 JSON。它们不创建 data root、Run 或 index，不访问 token/HTTP。`workflow-plan` 只描述 integrated capability、availability、request cost、budget 和 blocker；`RESEARCH_ONLY` step 的 request cost 固定为 0，且不会假装可执行。

`system-model-compile/validate/diff` 也属于 Local Depth。Compile 只读取显式 Run refs 和其声明 Artifact，输出独立快照目录；Validate/Diff 不加载 transport。System Model diff 的缺失语义固定为 `NOT_OBSERVED_IN_AFTER_INPUTS`。

## Plan-only

`collect --plan-only` 只做本地解析和校验，不创建 Run、不写 `.inflight/`、不写 `runs.jsonl`、不访问 HTTP。无效 source Run、item_ref、source kind 或时间形状会返回：

```json
{
  "schema_version": 1,
  "command": "collect",
  "status": "BLOCKED",
  "reason_code": "INVALID_SOURCE_REF",
  "live_request_count": 0
}
```

Ready plan 使用 `expected_logical_request_count`。真实 Run Manifest 的 `live_request_count` 是实际 HTTP attempts，retry/auth replay 会增加它。

## Startup and Auth

每次 CLI startup 会先冻结 confirmed stale `.inflight/` Run 为 `INTERRUPTED`，不会冻结 active owner PID。

默认生产 transport 缺少 `TINGYUN_AUTHORIZATION` 时，`discover` / `collect` / `source` / `investigate` 返回 `BLOCKED / AUTH_NOT_CONFIGURED`，且 `live_request_count = 0`。
