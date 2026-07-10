# Tingyun CLI v1

听云 APM 调查 CLI v1 是一个面向 Agent 的只读事实获取工具。它的核心资产不是终端表格或诊断报告，而是每次真实访问后留下的不可变 Run、Raw Wire Evidence、Normalized Evidence、Coverage 和调查血缘。

当前状态：`Core Golden Path Live-Validated + Integrated Investigation Depth`。Live-validated 只限定已测试的 Core 目标、时间窗口和 runtime version；新 Advanced Source Capabilities 依据既有协议证据分级，不声明全部 Live-Proven。

## 四层入口

- **Core Golden Path**：`discover`、`collect`、`inspect candidates`、`investigate`；只读服务端并创建不可变 Run（`inspect` 除外）。
- **Advanced Read-only Source Surface**：`source ...`；一次一个固定 READ recipe，创建 SOURCE Run。
- **Local Investigation Depth**：`depth ...`；完全本地，0 HTTP、0 Run。
- **Workflow Plans**：`depth workflow-plan ...`；只生成确定性计划，不自动执行任何服务端请求。

## 是什么

- Agent-first：输出稳定 JSON，方便 Agent 调用和读取。
- Evidence Package-first：`collect` 生成固定核心证据包。
- Immutable Run：`discover` / `collect` / `investigate` 每次都创建新 Run。
- Advanced Source：显式 `source` 命令一次执行一个有界只读 recipe，并创建不可变 `SOURCE` Run。
- Local Investigation：`depth` 原语和 workflow plan 只处理本地 JSON，0 HTTP、0 Run。
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
tingyun source trace-exceptions --source-run-id run-... --source-item-ref item-0001 --time-context last_30m
```

除固定 page 1 / size 20 的 `alarm-events` 外，入口必须来自 `source_run_id + source_item_ref`。只有 response ranking 的既有精确血缘且通过 main actionType resolver 时才会暴露 `investigate_trace`；error/throughput ranking 不继承该证明。

## Local Investigation Depth

`depth` 提供 promotion matrix、trace candidates/selection、window narrowing/peak、path/error triage、window/tree comparison、external candidate analysis 和五个 workflow plans。所有 `depth` 命令不加载 transport、不创建 data root、不写 `.inflight/` 或 `runs.jsonl`。workflow plan 只返回确定性步骤、能力可用性、逻辑请求预算和 blockers，不自动执行。

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
