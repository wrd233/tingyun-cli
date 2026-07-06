# 听云能力协议基线

本协议基线只来自本地离线证据：6 组 AI-ready Session、2 份官方 API PDF、12 个导出文件。未连接听云环境，未发送 HTTP 请求，未实现 CLI、HTTP 客户端、写操作执行器或 Agent/LLM 系统。旧 CLI/catalog/snapshot/命令树未作为约束。

## 覆盖基线

- `sessions_processed`: 6/6
- `session_files_inspected`: 2943/2943
- `network_records_scanned`: 1493/1493
- `observed_method_path_all`: 216
- `observed_service_method_path_catalogued`: 202
- `static_or_ui_records_scanned_not_catalogued`: 47
- `documented_endpoint_method_path_catalogued`: 224
- `official_documents_inventoried`: 2/2
- `export_files_inspected`: 12/12
- `export_sheets_inspected`: 12
- `catalogued_endpoint_entries`: 390
- `identified_variants`: 431

## Endpoint / Variant 原则

Endpoint 以 `method + path` 为总账键；同一路径仅在判别参数改变业务语义、请求/响应结构实质变化或下游血缘不同时拆 Variant。普通 ID、时间窗口、分页、排序方向、搜索词和过滤值不单独拆 Variant。官方文档与真实 Session 不自动合并为 fallback；只有 exact `method + path` 共享同一合同。

三条独立分类轴固定为 `access`、`role`、`verification`。`VERIFIED` 需要真实请求、可解释响应、关键输入/响应字段、下游用途和 Evidence Reference；空列表只证明 endpoint/envelope，不证明 item 字段。

## Shared Wire Conventions

- Base URL：真实材料中出现内部 origin，协议资产中统一记为 `redacted_internal_origin`，不写入本机绝对路径、Cookie、Token 或 Authorization 值。
- 编码：大量 POST 使用 `application/x-www-form-urlencoded`；部分保存/配置接口使用 JSON body；GET 使用 query string。每个 Endpoint 的实际 content-type 和参数 presence 以 `endpoint-contracts.yaml` 为准。
- 响应包络：常见 `code/status/success/msg/data`，但不同模块存在 `status` 与 `code` 混用；不能仅凭 HTTP 200 判断业务成功。
- 时间：常见 `endTime`、`timePeriod`、`beginTime`、`queryTimestamp`，单位和语义必须逐 Endpoint 验证。
- 分页：常见 `pageNumber/pageSize` 和 `pageNum/pageSize`；结构资源目标是可完整枚举，高基数运行数据必须显式有界。

## 核心能力全景

### 资源与拓扑

业务系统、应用、实例、内部调用和外部服务已有真实 Session 证据。结构关系与运行边分开记录：业务系统包含应用属于 Structural Relation；应用调用应用/数据库/NoSQL/MQ/外部服务属于 Observed Runtime Edge，必须带 Time Context。其他业务系统默认只保留一跳边界，具体 Trace 可沿真实调用链继续。

### 性能与运行指标

核心 Metric 保留最小统计身份：`scope`、`semantic`、`aggregation`、`unit`、`time_context`、`shape`。导出文件证明用户可见统计语义，例如 P50/P75/P95/P99、吞吐率、请求数、错误率、慢次数、异常次数，但不反推 Wire 字段或排序参数。运行对象清单不再合并为单一 Capability：近期请求统计、事务、服务接口、外部调用和组件操作分别按真实 Endpoint 边界建模。

### 问题溯源

已观察到告警入口、Action/运行对象身份桥梁和已知 Trace 入口。强证据链包括 `nalarm-api/event/traceList`、`nalarm-api/event/trace`、动作概览 deep link、`server-api/action/get/{observedActionId}`、`server-api/action/alias/{observedActionId}`、`server-api/action/trace/detail`、`callTree` 和 `exceptions`。Stack、Agent Context 和日志搜索作为 Trace 深挖补充能力记录；缺口是部分运行清单到 traceGuid 的来源仍需后续 Capture 补强。

## 能力覆盖矩阵

| 分类 | 分支 | 状态 | Capability | Recipe | Gap |
|---|---|---|---|---|---|
| 资源与拓扑 | 业务系统发现 | VERIFIED | `list_business_systems` | `scan_business_system` | `` |
| 资源与拓扑 | 服务组 | DOCUMENTED_ONLY | `` | `` | `gap_service_group_identity` |
| 资源与拓扑 | 应用 | VERIFIED | `read_application_overview` | `scan_business_system` | `` |
| 资源与拓扑 | 实例 | VERIFIED | `read_application_overview` | `scan_business_system` | `` |
| 资源与拓扑 | 主机 | PARTIALLY_VERIFIED | `read_application_overview` | `scan_business_system` | `gap_host_process_agent_depth` |
| 资源与拓扑 | 进程 | PARTIALLY_VERIFIED | `get_trace_agent_context` | `trace_investigation` | `gap_host_process_agent_depth` |
| 资源与拓扑 | Agent | PARTIALLY_VERIFIED | `get_trace_agent_context` | `trace_investigation` | `gap_host_process_agent_depth` |
| 资源与拓扑 | 容器 / Pod / Namespace | NOT_FOUND | `` | `` | `gap_container_pod_namespace` |
| 资源与拓扑 | 内部调用 | VERIFIED | `read_business_topology` | `scan_business_system` | `` |
| 资源与拓扑 | 数据库 | PARTIALLY_VERIFIED | `list_component_operations` | `scan_business_system` | `gap_database_nosql_mq_metrics` |
| 资源与拓扑 | NoSQL | PARTIALLY_VERIFIED | `list_component_operations` | `scan_business_system` | `gap_database_nosql_mq_metrics` |
| 资源与拓扑 | MQ | DOCUMENTED_ONLY | `list_component_operations` | `scan_business_system` | `gap_database_nosql_mq_metrics` |
| 资源与拓扑 | 外部服务 | VERIFIED | `list_external_calls` | `scan_business_system` | `` |
| 资源与拓扑 | 跨业务系统边界 | PARTIALLY_VERIFIED | `read_business_topology` | `scan_business_system` | `gap_cross_system_boundary` |
| 性能与运行指标 | 业务系统 | VERIFIED | `read_business_topology` | `scan_business_system` | `` |
| 性能与运行指标 | 应用 | VERIFIED | `read_application_overview` | `scan_business_system` | `` |
| 性能与运行指标 | 实例 | PARTIALLY_VERIFIED | `read_application_overview` | `scan_business_system` | `` |
| 性能与运行指标 | 事务 / 请求 | PARTIALLY_VERIFIED | `list_transactions` | `scan_business_system` | `` |
| 性能与运行指标 | 服务接口 | PARTIALLY_VERIFIED | `list_service_interfaces` | `scan_business_system` | `` |
| 性能与运行指标 | 调用边 | VERIFIED | `read_business_topology` | `scan_business_system` | `` |
| 性能与运行指标 | 数据库 / NoSQL / MQ | PARTIALLY_VERIFIED | `list_component_operations` | `scan_business_system` | `gap_database_nosql_mq_metrics` |
| 性能与运行指标 | 外部调用 | VERIFIED | `list_external_calls` | `scan_business_system` | `` |
| 性能与运行指标 | 概览 | VERIFIED | `read_application_overview` | `scan_business_system` | `` |
| 性能与运行指标 | 时间趋势 | VERIFIED | `read_performance_timeseries` | `scan_business_system` | `` |
| 性能与运行指标 | 分位值 | VERIFIED | `read_performance_timeseries` | `scan_business_system` | `` |
| 性能与运行指标 | Top / Ranking | VERIFIED | `list_recent_requests` | `scan_business_system` | `` |
| 性能与运行指标 | 请求统计清单 | VERIFIED | `list_recent_requests` | `scan_business_system` | `` |
| 问题溯源 | 告警入口 | VERIFIED | `list_alarm_events` | `alarm_to_trace` | `` |
| 问题溯源 | Action / 运行对象身份 | PARTIALLY_VERIFIED | `resolve_action_context` | `alarm_to_trace` | `gap_runtime_to_trace_list` |
| 问题溯源 | 运行对象入口 | PARTIALLY_VERIFIED | `list_transactions` | `alarm_to_trace` | `gap_runtime_to_trace_list` |
| 问题溯源 | 近期清单入口 | PARTIALLY_VERIFIED | `list_recent_requests` | `scan_business_system` | `gap_recent_request_trace_selection` |
| 问题溯源 | 已知 Trace 入口 | VERIFIED | `get_trace_detail` | `trace_investigation` | `` |
| 问题溯源 | Trace 列表 | PARTIALLY_VERIFIED | `list_transactions` | `trace_investigation` | `gap_runtime_to_trace_list` |
| 问题溯源 | Trace Detail | VERIFIED | `get_trace_detail` | `trace_investigation` | `` |
| 问题溯源 | Call Tree | VERIFIED | `get_trace_call_tree` | `trace_investigation` | `` |
| 问题溯源 | Exception | VERIFIED | `list_trace_exceptions` | `trace_investigation` | `` |
| 问题溯源 | Stack | PARTIALLY_VERIFIED | `get_trace_stack` | `trace_investigation` | `gap_stack_non_empty` |

## 单 Session 连续真实回放

来源：`03-alarm-to-trace`，严格使用同一 Session 证据。真实业务名称、IP 和具体 ID 值在正文匿名；Endpoint、Wire 字段、调用顺序和 Evidence Reference 保留。

| 顺序 | 真实动作 | Endpoint | Evidence | 已证明血缘 |
|---:|---|---|---|---|
| 1 | 用户切换到过去 7 天告警列表 | POST /nalarm-api/event/traceList | request-0361 | 请求含 `pageNumber/pageSize/timePeriod/endTime/eventType/frequent/lang`；响应 `data.totalElements` 和 `data.content[]`，content 中有 `id`、`target.value`、`parentGroup[$application_id/$biz_system_id]`。 |
| 2 | 用户在告警详情页点击“跳转至详情” | POST /nalarm-api/event/trace | request-0366 | 请求 `id` 来自告警详情页 URL/选中告警上下文；响应再次给出 `target.value`、`parentGroup`、`alarmEventItems[].eventTraceId`。 |
| 3 | 新标签进入事务概览 Deep Link | `GET /server-api/action/get/{observedActionId}` / `GET /server-api/action/alias/{observedActionId}` | request-0380, request-0381 | 页面 URL 形如 `/web/server/action/overview/{bizSystemId}/{applicationId}/{actionId}`；`resolve_action_context` 只表达这些已观察 action id 与 applicationId、name/alias 的绑定，不建立通用 ID resolver。 |
| 4 | 读取事务指标与错误页 | POST /server-api/webaction/* 与 POST /server-api/error/smart/* | request-0400 - request-0464 | 事务概览、图表、错误分解和异常列表均在同一打开标签内发生；这证明告警可落到运行对象与问题页，但不证明所有错误项都有 traceGuid。 |
| 5 | 进入已知 Trace 详情 | `POST /server-api/action/trace/detail` | request-0476 | `get_trace_detail` 请求含 `bizSystemId/applicationId/actionType/traceGuid/queryTimestamp/timePeriod/endTime`；响应给出 `traceGuid/actionGuid/traceId/instanceId/duration/timeLine`。 |
| 6 | Trace 深挖 | `POST /server-api/action/trace/callTree`、`detail/exceptions`、`data/logTrace/searchLogTrace` | request-0490, request-0494, request-0496 | `get_trace_call_tree` 消费 detail 上下文中的 `traceId/actionGuid/queryTimestamp`；`list_trace_exceptions` 返回非空 HTTP Error Code；`search_trace_logs` 返回空列表，只作为 optional enrichment 证明 envelope。 |

## 跨 Session 组合能力路径

| 阶段 | Session | Capability | 连接级别 | 说明 |
|---|---|---|---|---|
| 业务系统拓扑扫描 | `01-business-system-top-down` | `list_business_systems` -> `read_business_topology` | VERIFIED CONNECTION | 同 Session 内业务系统、应用和调用边有连续请求证据。 |
| 应用深入指标 | `02-application-deep-dive` | `read_application_overview` -> `read_performance_timeseries` -> `list_recent_requests` / `list_transactions` / `list_external_calls` | PROTOCOL-COMPATIBLE | 与 01 使用同类 `server-api` Endpoint 和相同对象类型；不是一次真实连续操作。 |
| 告警到 Trace | `03-alarm-to-trace` | `list_alarm_events` -> `read_alarm_event_detail` -> `resolve_action_context` -> `get_trace_detail` -> `get_trace_call_tree` | VERIFIED CONNECTION WITH GAPS | 同 Session 内存在告警、运行对象身份桥梁和 Trace 深挖链路；运行清单 item 到 traceGuid 的通用选择仍是 Gap。 |
| 写能力证据保存 | `04/05/06` | `manage_business_settings` / `manage_anomaly_detection_policy` / `manage_alarm_rules` | EVIDENCE PRESERVED | 写能力保留为 Endpoint Contract 与 Capability 证据；不再作为正式业务 Recipe，不参与自动执行。 |

## 导出字段语义对照

| Export 字段 | Normalized 语义 | 证据文件 | 证明范围 |
|---|---|---|---|
| Apdex | apdex | download-0005/0006/0007-0010 | display_only |
| responseP50 / 响应时间中位数(ms) | response_time_percentile_p50 | download-0005/0006/0007-0010 | display_only |
| 响应时间 P75/P95/P99 (ms) | response_time_percentile_p75_p95_p99 | download-0007-0010 | display_only |
| 吞吐率 (/s) / 吞吐率(tps) | throughput_per_second | multiple csv | display_only |
| 请求数 | request_count | multiple csv/xlsx | display_only |
| 错误率(%) / 错误率 | error_rate | multiple csv/xlsx | display_only |
| 错误次数 / 错误数 | error_count | multiple csv/xlsx | display_only |
| 慢次数 | slow_count | multiple csv | display_only |
| 异常次数 | exception_count | download-0007-0010 | display_only |
| 总耗时(ms) / 耗时百分比(%) | duration_total_ms / duration_ratio | download-0011/0012/0013 | display_only |

## 增量维护方法

新证据进入后：登记 `sources/README.md`，100% 扫描新材料，与既有 `method + path` / Variant 对照，更新 observed scope 与字段观察并集。只有真实 Capture 证明后才升级 verification；Agent/LLM 结论不能直接升级为 VERIFIED；新环境路径不同则新增 observed variant 或新 Endpoint；不静默覆盖旧环境观察。
