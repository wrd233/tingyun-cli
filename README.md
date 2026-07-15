# Tingyun CLI v1.2

听云 APM 调查 CLI v1 是一个面向 Agent 的只读事实获取工具。它的核心资产不是终端表格或诊断报告，而是每次真实访问后留下的不可变 Run、Raw Wire Evidence、Normalized Evidence、Coverage 和调查血缘。

当前状态：`Core Golden Path Live-Validated + Research Convergence + Evidence-backed Living System Model v0`。Live-validated 只限定已测试的 Core 目标、时间窗口和 runtime version；Advanced Source 逐项依据协议证据晋升，不声明全部 Live-Proven。

Agent 首先读 `AGENT.md`。协议能力、验证等级、Runtime promotion、Workflow 和 Gap 的轻量入口是 `research/generated/research-index.json`；它由四个 canonical protocol 文件确定性生成，不是第二份手工总账。

## 五层入口

- **Core Golden Path**：`discover`、`collect`、`inspect candidates`、`investigate`；只读服务端并创建不可变 Run（`inspect` 除外）。
- **Advanced Read-only Source Surface**：`source ...`；一次一个固定 READ recipe，创建 SOURCE Run。
- **Local Investigation Depth**：`depth ...`；完全本地，0 HTTP、0 Run。
- **Workflow Plans**：`depth workflow-plan ...`；只生成确定性计划，不自动执行任何服务端请求。
- **Deterministic Evidence Composition / System Model**：`depth evidence-compile/evidence-validate` 面向调查级 Evidence Map；`depth system-model-compile/system-model-validate/system-model-diff` 面向系统级认知快照。全部 0 HTTP、0 Run。

## 是什么

- Agent-first：输出稳定 JSON，方便 Agent 调用和读取。
- Evidence Package-first：`collect` 生成固定核心证据包。
- Immutable Run：`discover` / `collect` / `investigate` 每次都创建新 Run。
- Advanced Source：显式 `source` 命令一次执行一个有界只读 recipe，并创建不可变 `SOURCE` Run。
- Local Investigation：`depth` 原语、workflow plan、Evidence Composition 和 System Model 只处理本地 JSON / immutable Runs，0 HTTP、0 Run。
- Read-only：Runtime 只允许已进入 Stable Surface 的读路径。
- Branch-aware：Evidence Item 只在身份完整且 Action 已验证时暴露 `available_actions`。
- Runtime-contract-hardened：失败步骤会形成 `FAILED` Artifact；成功空数据才是 `EMPTY`；`derived_from` 指向最终支撑 Raw 记录。

## 不是什么

它不是诊断报告生成器、自动根因分析器、通用 Endpoint Executor、Capability Runner、Workflow Engine、队列系统、SQLite 数据仓库或 Candidate 查询引擎。

## 安装

```bash
python3 -m pip install -e .
```

也可以直接在仓库内运行：

```bash
PYTHONPATH=src python3 -m tingyun_cli --help
```

## 配置

默认读取环境变量：

```bash
export TINGYUN_BASE_URL="https://your-tingyun-host"
export TINGYUN_DATA_ROOT=".tingyun-runs"
export TINGYUN_AUTHORIZATION="Bearer <token>"
```

或使用 JSON 配置文件：

```json
{
  "base_url": "https://your-tingyun-host",
  "data_root": ".tingyun-runs",
  "min_request_interval_seconds": 2
}
```

凭据只从环境读取，不写入 Run、stdout、`runs.jsonl` 或导出包。

## 最短工作流

```bash
tingyun discover --query "billing"
tingyun collect --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
tingyun inspect candidates top --run-id run-... --metric p99 --limit 10
tingyun investigate --source-run-id run-... --source-item-ref item-0001 --action investigate_trace
tingyun investigate --source-run-id run-... --source-item-ref item-0001 --action inspect_call_tree
```

Live 命令 stdout 只输出 Run Receipt。完整证据从 `manifest_path` 指向的 Run 中读取。

Core Collect 始终保持 topology、response performance、request-overview candidates 三个逻辑请求。error/throughput series 不会隐式加入默认路径。

## Advanced Source Surface

这些命令是显式高级读取，不属于默认 Golden Path；每次调用只执行一个串行 READ recipe，并复用 Core 的 auth、retry、pacing、Raw-before-Normalized、FAILED/EMPTY 和 immutable Run 合同：

```bash
tingyun source performance-error-series --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
tingyun source performance-throughput-series --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
tingyun source alarm-events --time-context last_30m
tingyun source alarm-detail --source-run-id run-... --source-item-ref alarm-event-0001 --time-context last_30m
tingyun source alarm-metric-series --source-run-id run-... --source-item-ref alarm-detail-0001 --time-context last_30m
tingyun source recent-requests --source-run-id run-... --source-item-ref item-0001 --time-context last_30m --ranking response
tingyun source application-instances --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
tingyun source external-calls --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
tingyun source trace-exceptions --source-run-id run-... --source-item-ref trace-node-0001 --time-context last_30m
tingyun source trace-stack --source-run-id run-... --source-item-ref trace-node-0001 --time-context last_30m
```

除固定 page 1 / size 20 的 `alarm-events` 外，入口必须来自 `source_run_id + source_item_ref`。告警详情会保留数组型 parentGroup，并为每个 `metrics[]` 生成独立、可选的 metric identity；只有 `$$transaction` target 会保留 Capture 已证明的 actionId 关系。`trace-exceptions` 与 `trace-stack` 都只接受 Call Tree 产出的 exact `trace_tree_node` item，其身份由 Trace Detail 的 traceId/bizSystemId/queryTimestamp 与 Call Tree 的 treeId 组合；每次只读取一个显式节点，不从普通 Trace item 猜节点、不遍历树。Stack 的成功响应必须严格为 `data: array[string]`；HTTP 成功但结构漂移会生成带 `PROTOCOL_SHAPE_MISMATCH` 的 `FAILED` Artifact，而不是伪装成 `EMPTY`。只有 response ranking 的既有精确血缘且通过 main actionType resolver 时才会暴露 `investigate_trace`；error/throughput ranking 不继承该证明。

每个成熟 Evidence Item 继续保留兼容的 `available_actions` 字符串列表，并新增 `action_contracts` 与 `action_blockers`：前者声明 Live/Advanced surface、精确输入和单次逻辑请求预算，后者声明缺失身份或未证明边界。`can` 仍不表示推荐或自动执行。

## Local Investigation Depth

`depth` 提供 promotion matrix、trace candidates/selection、window narrowing/peak、path/error triage、window/tree comparison、external candidate analysis 和五个 workflow plans。所有 `depth` 命令不加载 transport、不创建 data root、不写 `.inflight/` 或 `runs.jsonl`。workflow plan 只返回确定性步骤、能力可用性、逻辑请求预算和 blockers，不自动执行。

Candidate 可先用确定性匹配定位，Trace 样本可与聚合指标分开评估：

```bash
tingyun inspect candidates match --run-id run-... --name "SpringController/example" --application "Example"
tingyun depth trace-sample-assess --candidate candidates.json --candidate-item-ref item-0001 --trace trace.json --alarm-metric response_time
```

匹配只使用 exact/substring/route 等稳定规则，不使用模糊相似度、Embedding 或 LLM。DubboProvider + `TX,IF` 在缺少直接 Live proof 时不暴露 `investigate_trace`，并以 `UNRESOLVED_TRACE_ACTION_TYPE` 关闭。

## Deterministic Evidence Composition

```bash
tingyun depth evidence-compile --manifest investigation-manifest.json --output-dir compiled
tingyun depth evidence-validate --compiled-dir compiled
```

编译器验证 Window、`source_run_id + item_ref`、canonical Incident、Trace target、Call Tree 和 Source role 血缘，输出 source of truth、Evidence Map、四层 coverage、validation、report readiness 和深层提取。相同 Manifest + Runs 必须产生 byte-stable 输出。它只编译证据并评估 readiness，不生成 Word/Markdown 报告、RCA 或下一步 Live 请求。

Manifest 与输出合同见 `docs/investigation-manifest.md`、`docs/evidence-composition.md` 和 `docs/report-readiness-contract.md`。

## Research Convergence

```bash
PYTHONPATH=src python3 research/tools/research_views.py generate
PYTHONPATH=src python3 research/tools/research_views.py check
PYTHONPATH=src python3 research/tools/research_views.py diff --before old/research-index.json --after research/generated/research-index.json
```

`research/generated/research-index.json` 汇总 Endpoint/Variant/Capability/Workflow/Gap/Runtime 的可追踪关系、分布、孤立合同、source hashes 和 health；`research-overview.md` 是人工导航。维护边界见 `docs/research-maintenance.md`。

## Evidence-backed Living System Model v0

```bash
tingyun --data-root .tingyun-runs depth system-model-compile --manifest system-model-manifest.json --output-dir model-a
tingyun depth system-model-validate --compiled-dir model-a
tingyun depth system-model-diff --before model-a/snapshot.json --after model-b/snapshot.json
```

System Model 由显式 immutable Run refs 编译，复用 Run/Artifact/Evidence ref、Call Tree 提取与 schema validation。它只表达已观察结构、windowed runtime relations、freshness、coverage、conflict 和 diff；不补造实体、不把未观察到解释为删除，也不生成 RCA 或报告。完整合同见 `docs/system-model.md`。

## Run 位置

默认目录：

```text
.tingyun-runs/
├── runs/
├── .inflight/
├── runs.jsonl
└── exports/
```

`runs/<run-id>/manifest.json` 是入口，`raw/` 保存非敏感请求和响应记录，`evidence/` 保存 Agent 默认消费的归一化证据。

## 本地查看 Candidate

```bash
tingyun inspect candidates all --run-id run-...
tingyun inspect candidates top --run-id run-... --metric p99 --limit 20
tingyun inspect candidates filter --run-id run-... --metric error_rate --operator ">" --value 5
```

`inspect` 不访问服务端，不创建 Run，不写 `runs.jsonl`。`plan-only` 也是纯本地路径；无效 source、item_ref、kind 或时间形状会返回 machine-readable `BLOCKED` JSON，不创建 Run、不写 index、不访问 HTTP。

如果 Dataset 中所有行都缺少被请求的稳定 metric，`inspect candidates top/filter` 会返回本地错误，而不是按无意义的缺省值排序。

## 运行时语义

- `SUCCESS`：请求成功并得到可信事实。
- `EMPTY`：请求成功，但该领域没有可信域数据。
- `FAILED`：请求已尝试，但传输、HTTP 或业务语义失败，无法得到可信事实。
- `PARTIAL`：Live Run 已完成并落盘，但至少一个 required Artifact 是 `FAILED` 或 `BLOCKED`。
- `BLOCKED`：请求未开始，因为 source、action、time、lock 或 safety 前置条件不满足。

Preflight 中的 `expected_logical_request_count` 表示计划中的逻辑请求数；Manifest 中的 `live_request_count` 表示实际发送并已持久化 raw request 的 HTTP attempt 数。一次 transient retry 或 auth replay 都会增加实际 attempt 计数。

CLI 启动会先扫描 `.inflight/`，只冻结确认 stale 的 Run 为 `INTERRUPTED`，当前进程仍活跃的 inflight Run 不会被修改。默认生产 transport 缺少 `TINGYUN_AUTHORIZATION` 时，`discover` / `collect` / `investigate` 会在 HTTP 前返回 `BLOCKED / AUTH_NOT_CONFIGURED`。

## 设计基线

- `docs/requirements/tingyun-cli-v1-detailed-design.md`
- `docs/requirements/tingyun-cli-v1-decisions-01-60.md`
- `research/protocol/`
- `docs/runtime-surface.md`
- `docs/evidence-schema-depth.md`
- `docs/investigation-guide.md`
- `docs/protocol-promotion-matrix.md`
- `docs/research-maintenance.md`
- `docs/action-contract.md`
- `docs/system-model.md`
