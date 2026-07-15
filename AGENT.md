# Agent Operating Guide

## 从这里开始

1. 先读本文件建立 Runtime 心智模型。
2. 判断能力成熟度、相关 Workflow/Gap 或 Runtime promotion 时，读 `research/generated/research-index.json`；不要扫描 6 万行 Endpoint ledger。
3. Live 调查只使用 Evidence Item 的 `available_actions`；同时读取 `action_contracts` 的 surface/input/budget 和 `action_blockers` 的 reason/missing fields。
4. 调查级合并使用 Evidence Composition；跨多个显式 Run 的系统级认知使用 System Model。两者都不自动执行 Live 请求。

## 五层入口

- Core Golden Path：`discover -> collect -> inspect candidates -> investigate_trace -> inspect_call_tree`，其中 Live 命令只读服务端并创建不可变 Run。
- Advanced Source：`source ...`，一次执行一个显式 READ recipe 并创建 SOURCE Run。
- Local Investigation Depth：`depth ...`，0 HTTP、0 Run。
- Workflow Plans：`depth workflow-plan ...`，只输出计划、预算和 blocker，不执行计划。
- Deterministic Evidence Composition / System Model：`depth evidence-compile/evidence-validate` 生成调查级 Evidence Map；`depth system-model-compile/system-model-validate/system-model-diff` 生成和比较系统级快照。全部 0 HTTP、0 Run。

## Alarm-driven exact investigation

```text
Alarm Seed
-> exact historical Window
-> collect
-> inspect candidates match
-> exact source_run_id + item_ref
-> investigate_trace
-> trace-sample-assess
-> inspect_call_tree
-> evidence-compile
-> evidence-validate
```

Manifest 必须显式绑定 Seed、Incident、Window 和每个 Run；不要按名称连接。错目标 Trace 即使 HTTP 成功，也只能进入 rejected audit，不能进入 Incident Evidence Map。正常 Trace 样本与异常 Candidate aggregate 可以同时成立，必须保留为 counter-signal。

## Golden Path

1. 先运行 `discover`，得到 Discovery Run。
2. 读取 Receipt 中的 `manifest_path`。
3. 从 `evidence/targets.json` 选择一个 `business_system_candidate` 的 `item_ref`。
4. 用 `collect --source-run-id ... --source-item-ref ... --time-context ...` 生成 Core Evidence Run。
5. 先读 `manifest.json`，再读 `identity.json`、`topology.json`、`performance.json`、`candidates.json`。
   - `PARTIAL` Run 仍是可审计结果；逐个读取 Artifact status 和 `coverage.json`，不要丢弃成功证据。
   - `FAILED` Artifact 表示该 step 已尝试并有 raw response/error 支撑；`EMPTY` 才表示成功查询后的无数据。
6. 如需本地排序或筛选，使用 `inspect candidates all/top/filter`。
7. 只从 Evidence Item 的 `available_actions` 中 exact 选择 Action；执行前核对同 item 的 `action_contracts[].input`、surface 和 `logical_request_budget`。若没有 Action，读取 `action_blockers`，不得自行补身份。
8. 用 `investigate --source-run-id ... --source-item-ref ... --action ...` 生成 Child Run。
9. Candidate 的 `source_run_id` 指向创建它的 Collect Run。直接复制 `inspect` 输出中的 `source_run_id + item_ref`，不要改成父 Discovery Run。
10. 只有 Core 证据不足时才显式调用 `source`；每次只选一个 source recipe，读取其独立 SOURCE Run。
11. 对已有 Evidence 做 narrowing、selection、compare、diff、triage 或 workflow planning 时使用 `depth`；这些命令 0 HTTP、0 Run。

## 必须遵守

- 不要传裸 `bizSystemId`、`applicationId`、`actionId`、`traceId` 作为调查入口。
- 不要通过名称模糊匹配补身份。
- 不要把 `available_actions` 理解成推荐，只表示 `can`。
- 不要把 Candidate 的 `row_count == 1000` 当作全量证明。
- 不要把 CLI 的 `SUCCESS/PARTIAL/BLOCKED` 当作诊断结论。
- 不要要求 CLI 输出报告或根因判断。
- 不要把 `error_rate` 当 ratio；CLI 中 5% 写作 `--value 5`。
- 不要把 Trace proof 当成 Navigation proof。`BG` 和 `TX,IF` 可有 `investigate_trace`，但没有独立 route proof 时没有内部 URL。
- 不要把 Advanced Source 当成 Core Golden Path，也不要声称新 source 全部 Live-Proven。
- 不要把 `overview.max` 解释成单请求最大耗时；它仍为 UNKNOWN。
- 不要把 fixed-duration cluster 当根因；它只是 candidate signal。

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

Advanced Read-only Source Surface：performance error/throughput series、alarm events/detail/metric、recent request rankings、application instances、external calls、trace exceptions、exact node stack。它们只通过固定 source recipe 进入，不是 generic endpoint runner。

Local-only Surface：promotion matrix、trace candidates/selection、window narrowing/peak、path/error triage、window/instance/tree compare、external candidate analysis，以及五个 bounded workflow plans。

SQL、Logs、NoSQL、MQ 等保留在研究协议中；独立 Stack 只在 exact `trace_tree_node` 上以 `source trace-stack` 晋升，不允许普通 Trace、猜 node 或 fan-out。

## System Model 使用边界

- Manifest 必须显式列出 `run_refs`、`snapshot_id`、`as_of` 和 freshness threshold。
- Compile 只接受 Run manifest 声明的 Artifact，核对 status、Raw refs 和可追溯身份。
- 稳定归属关系标记 `STABLE_OWNERSHIP_OBSERVATION`；Trace/Call Tree/External 等运行边标记 `WINDOWED_RUNTIME_OBSERVATION` 并携带 time context。
- Diff 的 `not_observed` 只表示 after inputs 未观察到，禁止解释为删除、下线或根因。
- Model 的 `PARTIAL/STALE/UNKNOWN` 是证据覆盖语义，不是系统健康诊断。

`investigate_trace` 使用 semantic kind + requestType resolver：Web `WEB -> WEB`、Web `TX -> TX`、Web `TX,IF -> TX`、Background `BG -> BG`。DubboProvider `TX,IF` 和其他未知 composite 不猜测，也不暴露 action。

即使旧 Run 中某个 Item 手工包含 `available_actions`，`investigate` 仍会在发起 HTTP 前重新校验 action-specific wire identity 和 resolver；不完整或未验证则生成 `BLOCKED / ACTION_IDENTITY_INCOMPLETE`，且 `live_request_count = 0`。

默认生产 transport 缺少 `TINGYUN_AUTHORIZATION` 时，Live command 会在 HTTP 前返回 `BLOCKED / AUTH_NOT_CONFIGURED`。CLI startup 会自动冻结 confirmed stale `.inflight/` Run，但不会冻结 active owner PID。
