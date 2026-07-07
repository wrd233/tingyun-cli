# Tingyun CLI v1

听云 APM 调查 CLI v1 是一个面向 Agent 的只读事实获取工具。它的核心资产不是终端表格或诊断报告，而是每次真实访问后留下的不可变 Run、Raw Wire Evidence、Normalized Evidence、Coverage 和调查血缘。

## 是什么

- Agent-first：输出稳定 JSON，方便 Agent 调用和读取。
- Evidence Package-first：`collect` 生成固定核心证据包。
- Immutable Run：`discover` / `collect` / `investigate` 每次都创建新 Run。
- Read-only：Runtime 只允许已进入 Stable Surface 的读路径。
- Branch-aware：Evidence Item 只在身份完整且 Action 已验证时暴露 `available_actions`。

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
export TINGYUN_AUTHORIZATION="Bearer ..."
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
tingyun inspect candidates filter --run-id run-... --metric error_rate --operator ">" --value 0.05
```

`inspect` 不访问服务端，不创建 Run，不写 `runs.jsonl`。

## 设计基线

- `docs/requirements/tingyun-cli-v1-detailed-design.md`
- `docs/requirements/tingyun-cli-v1-decisions-01-60.md`
- `research/protocol/`
