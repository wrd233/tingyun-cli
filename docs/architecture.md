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

当前实现状态是 `Golden Path Live-Validated`，范围限定为已测试目标、时间窗口和 runtime version。它不声明 Production-ready 或 all-domain Live-Proven。

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

Runtime 在执行 `investigate` 前会重新检查 action-specific identity。当前仅有：

```text
investigate_trace: bizSystemId + applicationId + actionId + requestType
inspect_call_tree: bizSystemId + applicationId + actionGuid + traceId
```

`investigate_trace` 还必须通过唯一的 verified actionType resolver。当前仅编码已验证映射：`WEB -> WEB`、`TX -> TX`、`BG -> BG`、`TX,IF -> TX`。未知或顺序不同的 composite requestType 不暴露 Action，也不能靠旧 Evidence 中的手写 `available_actions` 绕过执行前校验。

Trace proof 与 Navigation proof 分开。`BG` 和 `TX,IF` 可以有 `investigate_trace`，但没有独立 route proof 时不输出内部 URL。

## Protocol vs Runtime

```text
Protocol can know more than Runtime may expose
```

协议保留 VERIFIED、PARTIALLY_VERIFIED、DOCUMENTED_ONLY 等材料。Runtime Stable Surface 只使用已验证的只读路径。

## Failure Boundary

HTTP execution returns a small execution result to the command layer. Normalized Artifacts use that result to record final raw provenance, attempt count, retry/auth metadata, and `FAILED` status when the request or upstream semantics failed.

`collect` keeps independent evidence steps separate. A failed topology, performance, or candidates step produces a finalized `PARTIAL` Run with successful sibling Artifacts preserved.

CLI startup runs a quick `.inflight/` recovery pass. Stale inflight Runs are frozen as `INTERRUPTED`; active owner PIDs are left untouched. Deterministic local validation runs before auth preparation and live-lock acquisition, so invalid source/time/action input is not hidden by `LIVE_EXECUTION_BUSY`.
