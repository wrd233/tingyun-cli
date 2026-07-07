# Agent Operating Guide

## Golden Path

1. 先运行 `discover`，得到 Discovery Run。
2. 读取 Receipt 中的 `manifest_path`。
3. 从 `evidence/targets.json` 选择一个 `business_system_candidate` 的 `item_ref`。
4. 用 `collect --source-run-id ... --source-item-ref ... --time-context ...` 生成 Core Evidence Run。
5. 先读 `manifest.json`，再读 `identity.json`、`topology.json`、`performance.json`、`candidates.json`。
   - `PARTIAL` Run 仍是可审计结果；逐个读取 Artifact status 和 `coverage.json`，不要丢弃成功证据。
   - `FAILED` Artifact 表示该 step 已尝试并有 raw response/error 支撑；`EMPTY` 才表示成功查询后的无数据。
6. 如需本地排序或筛选，使用 `inspect candidates all/top/filter`。
7. 只从 Evidence Item 的 `available_actions` 中 exact 选择 Action。
8. 用 `investigate --source-run-id ... --source-item-ref ... --action ...` 生成 Child Run。

## 必须遵守

- 不要传裸 `bizSystemId`、`applicationId`、`actionId`、`traceId` 作为调查入口。
- 不要通过名称模糊匹配补身份。
- 不要把 `available_actions` 理解成推荐，只表示 `can`。
- 不要把 Candidate 的 `row_count == 1000` 当作全量证明。
- 不要把 CLI 的 `SUCCESS/PARTIAL/BLOCKED` 当作诊断结论。
- 不要要求 CLI 输出报告或根因判断。

## 读取顺序

每个 Run 先读：

```text
manifest.json
coverage.json
```

再根据 `manifest.artifacts[]` 读取：

```text
evidence/*.json
```

只有需要审计请求/响应时才读：

```text
raw/*.json
```

## Stable Actions

当前 Runtime Stable Surface：

- `investigate_trace`：只从具备 `bizSystemId`、`applicationId`、`actionId`、`requestType` 的 Candidate Item 读取 Trace Detail。
- `inspect_call_tree`：只从具备 `bizSystemId`、`applicationId`、`actionGuid`、`traceId` 的 Trace Item 读取 Call Tree。

SQL、Stack、Logs、NoSQL、MQ 等保留在研究协议中；未进入 Runtime Stable Surface 前不要调用。

即使旧 Run 中某个 Item 手工包含 `available_actions`，`investigate` 仍会在发起 HTTP 前重新校验 action-specific wire identity；不完整则生成 `BLOCKED / ACTION_IDENTITY_INCOMPLETE`，且 `live_request_count = 0`。
