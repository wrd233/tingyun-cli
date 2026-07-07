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

## preflight.json

Preflight 是当前一次 live command 的冻结执行边界。第一条真实请求前写入，执行开始后不再修改。

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

## raw/

Raw 保存非敏感请求意图和响应/错误。请求记录在 HTTP 前写入，响应/错误在返回后立即写入，然后才做 Normalization。

永不保存 Authorization、Cookie、Token、Password 或 Secret。

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
```

Candidate 主来源是 `POST /server-api/graph/query/overview?request_overview`。`candidates.json` 保留实际获得的全部行，不做二次 Top N 裁剪。
