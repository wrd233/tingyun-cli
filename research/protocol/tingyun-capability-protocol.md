# 听云能力协议基线

本协议基线主体来自本地离线证据：8 组 Capture Session、2 份官方 API PDF、12 个既有导出文件，并吸收 2026-07-07 已完成的低频只读 live validation 结论。新增两组 2026-07-15 私有 Raw Capture 只在本地分析，未提交 Raw、内部 origin、个人信息或凭据。当前 v1 runtime 状态为 `Core Golden Path Live-Validated + Integrated Investigation Depth`，范围限定为已测试目标、时间窗口和 runtime version；Advanced Source 只按既有证据分级，不声明全部 Live-Proven。

Runtime 保持三层：Core Collect 固定 3 个逻辑请求；Advanced Source 每次只运行一个固定串行 READ recipe 并创建 SOURCE Run；本地 depth/workflow plan 为 0 HTTP、0 Run。WRITE/UNKNOWN 与 research-only endpoint 不进入生产安全面。

## 覆盖基线

- `sessions_processed`: 8/8
- `session_files_inspected`: 5246/5246
- `network_records_scanned`: 1995/1995
- `observed_method_path_all`: 226
- `observed_service_method_path_catalogued`: 212
- `static_or_ui_records_scanned_not_catalogued`: 47
- `documented_endpoint_method_path_catalogued`: 224
- `official_documents_inventoried`: 2/2
- `export_files_inspected`: 12/12
- `export_sheets_inspected`: 12
- `catalogued_endpoint_entries`: 400
- `identified_variants`: 442

## Endpoint / Variant 原则

Endpoint 以 `method + path` 为总账键；同一路径仅在判别参数改变业务语义、请求/响应结构实质变化或下游血缘不同时拆 Variant。普通 ID、时间窗口、分页、排序方向、搜索词和过滤值不单独拆 Variant。官方文档与真实 Session 不自动合并为 fallback；只有 exact `method + path` 共享同一合同。

三条独立分类轴固定为 `access`、`role`、`verification`。`VERIFIED` 需要真实请求、可解释响应、关键输入/响应字段、下游用途和 Evidence Reference；空列表只证明 endpoint/envelope，不证明 item 字段。

本轮增量使用更细的证据标签：`OBSERVED` 仅表示本次 UI journey 中出现；`VALUE_MATCHED` 表示两个可观察位置精确同值；`LIVE_VERIFIED` 表示已记录请求形状得到可解释且符合所述非空结构的真实响应；`CROSS_RUN_VERIFIED` 表示独立样本或路径重复证明；`UNRESOLVED` 保留缺失身份或稳定性。四个生命周期必须分开：Protocol-known、Live-observed/verified、Runtime-promoted。新 Endpoint 存在或一次成功不自动进入 CLI。

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

核心 Metric 保留最小统计身份：`scope`、`semantic`、`aggregation`、`unit`、`time_context`、`shape`。导出文件证明用户可见统计语义，例如 P50/P75/P95/P99、吞吐率、请求数、错误率、慢次数、异常次数，但不反推 Wire 字段或排序参数。运行对象清单不再合并为单一 Capability：近期请求统计、事务、服务接口、外部调用、组件操作和 v1 Candidate Dataset 分别按真实 Endpoint 边界建模。`application/charts/response` 的 business-system scope shape 已由 live run `20260707-0400-micro-shape-scope-validation` 确认：`businessType="BIZ_SYSTEM"` 可返回响应时间、P50、P80、P95、P99 五组 ms series；该结论不证明 `businessType` 可省略，也不外推到 application scope 或其他 chart endpoint。

Candidate Dataset 的 Primary Stable Source 已确定为 `POST /server-api/graph/query/overview?request_overview`。真实 Session `session-acce84d0-9163-41a5-b151-9bec4b904b5f` 中四组 request_overview List API 返回 819、862、1000、1000 行，字段包含 `actionId`、`applicationId`、`systemId`、`actionName`、`applicationName`、P50/P75/P95/P99、平均响应、吞吐、请求数、错误、慢请求和异常计数。`errorRate` 的 normalized runtime 单位是 percent，不是 ratio。对应 Export 只保留展示字段和指标，不能保留完整执行身份，因此 v1 Runtime 不再把 Export/Download 作为 Candidate fallback。返回 1000 行只记录为已观察边界，不证明全量。

Candidate -> Trace 的 v1.1 runtime resolver 以 `semantic_kind + wire requestType` 为输入：Web `WEB -> WEB`、Web `TX -> TX`、Web `TX,IF -> TX`、Background `BG -> BG`。同一 Web Candidate identity 的受控比较显示 `actionType="TX,IF"` 返回 200/404 no-match，而 `actionType="TX"` 成功返回 Trace identity；该证明不能外推到 DubboProvider。`DubboProvider + TX,IF` 保持 `UNRESOLVED_TRACE_ACTION_TYPE` 并关联 `gap_dubbo_provider_trace_action_type`。不得使用通用 `split(",")`，也不能把 `IF,TX`、`BG,IF`、`TX,BG` 等未知 composite 外推为可执行。Trace proof 与 Navigation proof 独立；只有 `LIVE_OBSERVED` 或 `DERIVED_FROM_VERIFIED_ROUTE` 链接可传播。

v1.1 的本地调查合同把 Candidate 匹配限定为 `EXACT/STRONG/WEAK/NOT_FOUND`，执行身份始终是 exact `collect_run_id + item_ref`。Trace target 必须独立检查 `source_run_id + source_item_ref`；成功的 wrong-target Trace 只进入 rejected audit。Trace 样本与 Candidate 聚合分别保留，输出 `ABNORMAL_ALIGNED/NORMAL_CONTRAST/UNKNOWN`，不输出根因。Exception Evidence 区分 thrown、logged error、`error=false` log event 与 unknown；Candidate `exception_count` 继续保持 UNKNOWN 语义。

Deterministic Evidence Composition 通过显式 Investigation Manifest 绑定 Alarm、Incident、Window、Candidate、Trace、Call Tree 与 Source，输出 source-of-truth、Evidence Map、coverage、validation、report readiness 和 deep extractions。相同 Manifest + immutable Runs 必须 byte-stable；编译器/验证器 0 HTTP、0 Run，不生成报告。`alarm-events` 当前请求与 13 次历史成功合同完全一致，因此没有修正版 Live 实验；`application-instances` 当前请求与 observed HTTP 500 同形，原因记录为 `gap_application_instances_http_500`，不能解释为无实例或权限问题。

### 问题溯源

已观察到告警入口、Action/运行对象身份桥梁、近期请求入口、Candidate direct Trace 入口和已知 Trace 入口。当前 Core Golden Path 是 `discover -> collect(request_overview candidates) -> inspect candidates -> investigate_trace -> inspect_call_tree`。Advanced Source 可通过固定 `recent-requests --ranking response` recipe 使用 business-system-scoped `responseList`；其 `content[].actionId` 精确进入 `trace/detail.request.actionId`，detail 再提供 `actionGuid` 与 `data.id(traceId)` 给 callTree。该证明不继承到 errorList/throughtList，也不把 responseList 变成 Core 路径。Trace Detail 内嵌 exceptions/stack 与独立 `detail/exceptions` source Evidence 保持分离。

2026-07-15 Capture 进一步证明了四条边界清晰的路径。第一，`$$transaction` 告警详情的 target 与 parentGroup 身份被新标签页、Action lookup 和 `actionItemList` 精确消费；这只关闭告警入口身份 Gap，普通事务页面 cold start 仍开放。第二，告警详情的 `metrics[]`、target type、完整 event items 与策略上下文被 metric/chart 请求精确消费并返回非空 series。第三，链路追踪 `trace_current_overview.content[].id` 被 detail 精确消费为 `traceId`，detail 的 actionGuid/data.id 再进入 callTree；该 list-driven 路径不证明 DubboProvider direct actionType。第四，exceptions/stackTraces 是节点级分支，精确依赖 treeId、traceId、bizSystemId、queryTimestamp 与时间上下文，并得到非空异常和堆栈。v1.2 只把最后一条中的 stackTraces 以 exact node、单请求 SOURCE recipe 晋升；不晋升搜索路径、普通 Trace 输入或 fan-out。

事务错误分析中，聚合 list/detail 只形成发现入口；`exceptionStatistics.content[]` 才提供被 detail 精确消费的 traceGuid 等身份。`errorExport/creatTask` 创建服务端任务，分类为 WRITE，即使随后下载表格也不进入 READ Runtime。告警详情之后触发的 `event/read` 是已读状态 WRITE，不再混入详情读取 Capability；本轮未捕获 readFlag 前后回读。所有页面 URL 本轮仅 OBSERVED，因为未完成 reload/new-tab/cross-session verify。

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
| 性能与运行指标 | Candidate Dataset | VERIFIED | `list_request_overview_candidates` | `scan_business_system` | `` |
| 性能与运行指标 | Top / Ranking | VERIFIED | `list_recent_requests` | `scan_business_system` | `` |
| 性能与运行指标 | 请求统计清单 | VERIFIED | `list_recent_requests` | `scan_business_system` | `` |
| 性能与运行指标 | Business-System Response Time Series | VERIFIED | `read_performance_timeseries` | `scan_business_system` | `` |
| 问题溯源 | 告警入口 | VERIFIED | `list_alarm_events` | `alarm_to_trace` | `` |
| 问题溯源 | Action / 运行对象身份 | PARTIALLY_VERIFIED | `resolve_action_context` | `alarm_to_trace` | `gap_transaction_page_actionitem_cold_start` |
| 问题溯源 | 运行对象入口 | PARTIALLY_VERIFIED | `list_transactions` | `alarm_to_trace` | `gap_transaction_page_actionitem_cold_start` |
| 问题溯源 | 近期清单入口 | VERIFIED | `list_recent_requests` | `scan_business_system` | `` |
| 问题溯源 | 近期请求 → Trace | VERIFIED | `list_recent_requests` -> `get_trace_detail` -> `get_trace_call_tree` | `trace_investigation` | `` |
| 问题溯源 | 已知 Trace 入口 | VERIFIED | `get_trace_detail` | `trace_investigation` | `` |
| 问题溯源 | 链路追踪搜索 / Trace Candidate 列表 | VERIFIED | `search_trace_candidates` | `trace_search_to_detail` | `` |
| 问题溯源 | 普通事务页面 Trace 列表 | PARTIALLY_VERIFIED | `list_transactions` | `trace_investigation` | `gap_transaction_page_actionitem_cold_start` |
| 问题溯源 | 错误/异常代表样本 | VERIFIED | `analyze_transaction_errors` | `alarm_to_trace` | `gap_error_analysis_error_to_trace` |
| 问题溯源 | Trace Detail | VERIFIED | `get_trace_detail` | `trace_investigation` | `` |
| 问题溯源 | Call Tree | VERIFIED | `get_trace_call_tree` | `trace_investigation` | `` |
| 问题溯源 | Exception | VERIFIED | `list_trace_exceptions` | `trace_investigation` | `` |
| 问题溯源 | Stack | VERIFIED | `get_trace_stack` | `trace_investigation` | `gap_stack_non_empty` |

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

## Cross-Run Composite Golden Path

| 阶段 | Wire 字段 / Endpoint | 证明范围 |
|---|---|---|
| Business System | `GET /server-api/data/business/getBusinessTree` | 发现业务系统身份；核心链按 business system scope 描述，不把未解释的 applicationId 写成必需输入。 |
| Business Topology | `POST /server-api/graph/queryBizDetailGraph` with `mergeGraph="1"` and `cascadingDisplay="1"` | live run `20260707-0400-micro-shape-scope-validation` 确认该完整字符串形态可执行，返回 12 个 structural nodes 和 27 条 time-windowed runtime edges；edge metrics 保留 wire spelling `response`、`throught`、`error`。不声明 `mergeGraph` 单字段导致上一轮 INTERNAL。 |
| Business-System Response Series | `POST /server-api/application/charts/response` with `businessType="BIZ_SYSTEM"` | 同一 micro run 确认 business-system scope 响应时间序列可执行，返回响应时间、P50、P80、P95、P99 五组 30 点 ms series，overview avg=22、max=160585。 |
| Same-Run Core Collect Raw Correction | first controlled Golden Path collect raw responses | 本地 reprocessing 证明旧 normalized `EMPTY` 是 normalizer 缺口：当前 topology normalizer 从同一 Raw 得到 SUCCESS、13 nodes、38 edges；performance normalizer 得到 SUCCESS、overview present、response_avg/P50/P80/P95/P99 各 30 点。旧 Run 不改写。 |
| Recent Request List | `POST /server-api/webaction/list/responseList` -> `response.data.content[].actionId` | `actionId` 是已验证的 recent-request item 输出；本结论只覆盖 responseList live sample，不自动扩展到 throughtList/errorList。 |
| Candidate Trace Detail | `POST /server-api/action/trace/detail` request `actionId` + verified `actionType` | v1.1 semantic resolver only: Web+WEB -> WEB、Web+TX -> TX、Background+BG -> BG、Web+TX,IF -> TX；未知 semantic/composite withheld。 |
| Recent Request Trace Detail | `POST /server-api/action/trace/detail` request `actionId` | research/protocol path: 当前 live-observed responseList shape 中，`actionId` 足以作为 detail 身份输入，无需先经 action/get 或 action/alias 转换为 actionGuid。 |
| Call Tree | `trace/detail.response.actionGuid` -> `callTree.request.actionGuid`; `trace/detail.response.data.id` -> `callTree.request.traceId` | 两个下游参数均为 exact value match；callTree 返回非空完整调用树。 |

本路径是 Live-Verified Composite / Cross-Run Composite：拓扑与性能来自 micro run `20260707-0400-micro-shape-scope-validation`，recent request -> trace -> callTree 来自上一轮 vertical slice。它表达协议兼容的可执行链路，不声称这些阶段来自一次不中断的连续用户操作。

Live run audit note：`/Users/wangrundong/Downloads/live.zip` 中的 run `20260707-0200-business-system-vertical-slice` 已只读审计。该 run 有 7 条 request-log、7 个 response 文件、summary 中 7 条 request，final report 覆盖 LIVE-001..LIVE-007；编号完整。`LIVE-002-response.json` business code 为 `INTERNAL`，但 `request-log.jsonl` 与 `live-run-summary.json` 误标 `SUCCESS`。`final-report.md` 的业务系统 fingerprint 与 summary/preflight hash 规则不一致；application fingerprint 一致。zip 中没有 `LIVE-xxx-request.json`，因此 exact request body 仍不能审计。`actionGuid.value == traceGuid.value` 仅记录为本次 live sample 观察，不建立永久语义等价、fallback 或自动互换规则。

## Live Evidence Audit Status

Evidence status 使用 `CONFIRMED`、`SUPPORTED`、`UNRESOLVED`、`CONTRADICTED`。上一轮 live run 的 request count 与 LIVE 编号完整性为 `CONFIRMED`；原始 JSON handoff 中 `LIVE-002` 状态语义、business-system fingerprint 一致性、preflight/request-log/summary sanitization 为 `CONTRADICTED`，已在 gitignored sanitized handoff copy 中修正；observed interval 17.0s 为 `CONFIRMED`。micro run `20260707-0400-micro-shape-scope-validation` 已补齐 `LIVE-001/002-request.json` 与 response pairs，status semantics 为 `PASS`，fingerprint consistency 为 `PASS`，sanitization 为 `PASS`，并通过 `run_end_time.txt` 与 request evidence 证明实际 RUN_END_TIME；剩余 handoff gap 是 `preflight.json` 仍保留 null run-end fields。后续 handoff 必须在 LIVE-001 前完成 sequence: confirm experiment -> generate RUN_END_TIME -> persist into `preflight.json` -> freeze preflight -> execute LIVE-001；`preflight.json` 是执行前最终网络请求快照，不是模板。

## 跨 Session 组合能力路径

| 阶段 | Session | Capability | 连接级别 | 说明 |
|---|---|---|---|---|
| 业务系统拓扑扫描 | `01-business-system-top-down` | `list_business_systems` -> `read_business_topology` | VERIFIED CONNECTION | 同 Session 内业务系统、应用和调用边有连续请求证据。 |
| 应用深入指标 | `02-application-deep-dive` + `20260707-0400-micro-shape-scope-validation` | `read_application_overview` -> `read_performance_timeseries` -> `list_recent_requests` / `list_transactions` / `list_external_calls` | LIVE-VERIFIED COMPOSITE | `application/charts/response` 的 business-system response-time series shape 已 live-confirmed；与 01 使用同类 `server-api` Endpoint 和相同对象类型，但不是一次真实连续操作。 |
| 近期请求到 Trace | `live_evidence_round_2_2026-07-07` | `list_recent_requests` -> `get_trace_detail` -> `get_trace_call_tree` | LIVE-VERIFIED CONNECTION | `responseList.content[].actionId` 直接进入 trace/detail，detail 输出 `actionGuid` 与 `data.id(traceId)` 进入 callTree。 |
| 告警到事务上下文 | `2026-07-15 private Capture` | `list_alarm_events` -> `read_alarm_event_detail` -> `resolve_action_context` -> `list_transactions` | VALUE-MATCHED CONNECTION | 仅对 `$$transaction` target 精确证明 action/application/business-system 身份；actionItemList 为空且普通事务页面 cold start 仍独立开放。 |
| Trace 搜索到详情 | `2026-07-15 private Capture` | `search_trace_candidates` -> `get_trace_detail` -> `get_trace_call_tree` | LIVE-VERIFIED CONNECTION | overview item `id` 进入 detail.traceId；该 list-driven 路径不证明 direct actionType resolver。 |
| 异常节点到 Stack | `2026-07-15 private Capture` | `get_trace_detail` -> `list_trace_exceptions` -> `get_trace_stack` | LIVE-VERIFIED CONNECTION | exceptions 与 stackTraces 共享 exact treeId/traceId，上游 queryTimestamp 绑定同一 Trace；Runtime 只以 exact node、单请求 SOURCE recipe 提升 exception 与 stack，不提升普通 Trace 输入、搜索或 fan-out。 |
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
