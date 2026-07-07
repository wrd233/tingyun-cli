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

## Inspect

```bash
tingyun inspect candidates all --run-id run-...
tingyun inspect candidates top --run-id run-... --metric p99 --limit 10
tingyun inspect candidates filter --run-id run-... --metric error_rate --operator ">" --value 0.05
```

`inspect` 是纯本地 JSON 视图，不创建 Run。
