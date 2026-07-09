# Tingyun CLI v1

听云 APM 调查 CLI v1 是一个面向 Agent 的只读事实获取工具。它的核心资产不是终端表格或诊断报告，而是每次真实访问后留下的不可变 Run、Raw Wire Evidence、Normalized Evidence、Coverage 和调查血缘。

当前状态：`Golden Path Live-Validated`，范围限定为已测试目标、时间窗口和 runtime version。它不声明 Production-ready 或 all-domain Live-Proven。

## 是什么

- Agent-first：输出稳定 JSON，方便 Agent 调用和读取。
- Evidence Package-first：`collect` 生成固定核心证据包。
- Immutable Run：`discover` / `collect` / `investigate` 每次都创建新 Run。
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
