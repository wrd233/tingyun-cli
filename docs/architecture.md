# Architecture

## Core Model

```text
discover
  -> Discovery Run
  -> Agent selects source item
collect
  -> Core Evidence Run
  -> Agent reads identity/topology/performance/candidates
investigate
  -> Child Run
  -> new evidence and available_actions
```

CLI 负责安全、准确、克制地获取事实并保存证据。Agent 负责判断哪些事实重要、如何组合分析、下一步查什么以及何时停止。

## Runtime Boundary

Runtime 只暴露：

```text
discover
collect
investigate
inspect
plan-only
sanitized-export
```

底层 Endpoint / Capability / Variant 是协议和 Recipe 内部构件，不作为默认 Agent Surface。

## Source Model

所有从 Evidence 继续的动作使用：

```text
source_run_id + source_item_ref
```

`item_ref` 是 Run-local opaque reference。完整身份是 `run_id + item_ref`。

## Available Actions

形成规则：

```text
item kind
+ required wire identity present
+ action stable
= available_actions
```

它只表示可以执行，不表示推荐、优先级或诊断理由。

## Protocol vs Runtime

```text
Protocol can know more than Runtime may expose
```

协议保留 VERIFIED、PARTIALLY_VERIFIED、DOCUMENTED_ONLY 等材料。Runtime Stable Surface 只使用已验证的只读路径。
