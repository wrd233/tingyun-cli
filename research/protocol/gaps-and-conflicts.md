# Gaps and Conflicts

本文件只记录未解决问题、冲突和未来 validation task。所有未知连接保留为 Gap，不在协议中补全。

## gap_service_group_identity: 服务组身份未由 Session 深度证明

- 已知事实：官方/页面语义出现服务组/分组概念，Session 中主要证明业务系统、应用、实例和调用边。
- 缺失证据：缺少服务组稳定 ID、枚举接口、与应用/业务系统的结构关系。
- 对能力影响：无法把服务组作为可完整枚举结构资源。
- 下一次 Capture 要补什么：下一次 Capture 专门进入服务组页面，记录列表、详情、应用成员、分页和保存前后读取。
- 成功判定条件：能证明 `service_group_id -> application_id[]` 或明确 NOT_FOUND。
- 禁止假设：不得按显示名或业务系统名合并服务组。
- related_capabilities:
  - `list_business_systems`
- related_recipes:
  - `scan_business_system`
- evidence_seed: `GET /server-api/data/business/getBusinessTree` 与业务系统树证据只能作为起点，不能替代服务组身份。

validation task:
- goal: 服务组身份未由 Session 深度证明
- starting context: 使用本轮 `research/protocol/endpoint-contracts.yaml` 中相关 Endpoint。
- exploration target: 下一次 Capture 专门进入服务组页面，记录列表、详情、应用成员、分页和保存前后读取。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 能证明 `service_group_id -> application_id[]` 或明确 NOT_FOUND。
- do not assume: 不得按显示名或业务系统名合并服务组。

## gap_cross_system_boundary: 跨业务系统边界未形成完整调用闭环

- 已知事实：业务系统拓扑和调用边可证明一跳运行边界，部分响应含 caller/callee 业务系统候选。
- 缺失证据：缺少跨业务系统调用从拓扑边进入下游应用、事务、Trace 的完整参数血缘。
- 对能力影响：跨业务系统边界只能 PARTIALLY_VERIFIED，不能声明任意跨系统递归扫描。
- 下一次 Capture 要补什么：从业务系统拓扑选择一条跨系统调用边，进入下游系统/应用/事务并抓取后续 Trace 或统计请求。
- 成功判定条件：证明 topology edge field -> downstream bizSystemId/applicationId/actionId/trace parameter。
- 禁止假设：不得按显示名、拓扑位置或 action name 推断跨系统身份等价。
- related_capabilities:
  - `read_business_topology`
  - `list_transactions`
  - `get_trace_detail`
- related_endpoints:
  - `ep_post_server_api_graph_querybizsystengraph`
  - `ep_post_server_api_graph_querybizdetailgraph`
- related_recipes:
  - `scan_business_system`
- evidence_seed: 从 `01-business-system-top-down` 的业务系统拓扑请求开始，沿同一 UI 点击补齐下游请求。
- request_shape_audit_2026-07-07:
  - evidence_status: CONTRADICTED for current status labeling; UNRESOLVED for exact live request body; CONFIRMED for historical successful shape.
  - historical successful endpoint/variant: `ep_post_server_api_graph_querybizdetailgraph#variant_default`.
  - historical successful shape: POST form body with `bizSystemId`, `timePeriod`, `endTime`, `mergeGraph`, `cascadingDisplay`, `lang`; observed successful examples include `mergeGraph=1,cascadingDisplay=1` and `mergeGraph=0,cascadingDisplay=1`.
  - live failed shape: `request-log.jsonl` records target `bizSystemId`, `RUN_END_TIME`, and `timePeriod=30`; exact `LIVE-002-request.json` is absent, so `mergeGraph` / `cascadingDisplay` presence is unauditable.
  - live status audit: `LIVE-002-response.json` has business `code=INTERNAL`; `request-log.jsonl` and `live-run-summary.json` incorrectly label result `SUCCESS`, while `final-report.md` correctly calls it INTERNAL error.
  - minimal likely diff to validate: historical graph discriminator presence (`mergeGraph=1` + `cascadingDisplay=1`) before treating INTERNAL as endpoint/runtime failure.

Micro Experiment A:
- goal: 验证 `queryBizDetailGraph` live INTERNAL 是否由缺失 historical graph discriminator field presence 导致。
- exact endpoint id: `ep_post_server_api_graph_querybizdetailgraph`
- exact variant id: `variant_default`
- known successful historical request shape: `POST /server-api/graph/queryBizDetailGraph` form body `bizSystemId=<target>`, `timePeriod=<fixed>`, `endTime=<RUN_END_TIME>`, `mergeGraph=1`, `cascadingDisplay=1`, `lang=zh_CN`.
- single field / presence difference to validate: use the historical `mergeGraph` + `cascadingDisplay` presence set; do not vary other fields.
- target scope: same business-system fingerprint used by the failed live run.
- time context: fixed persisted `RUN_END_TIME`; use one bounded window only.
- maximum requests: 1.
- stop conditions: stop after the first response; record transport_status, business_status, result, sanitized request, sanitized response, and do not retry variants.

validation task:
- goal: 跨业务系统边界未形成完整调用闭环
- starting context: `read_business_topology`，重点看 `ep_post_server_api_graph_querybizsystengraph` 和 `ep_post_server_api_graph_querybizdetailgraph`。
- exploration target: 从业务系统拓扑选择一条跨系统调用边，进入下游系统/应用/事务并抓取后续 Trace 或统计请求。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 证明 topology edge field -> downstream bizSystemId/applicationId/actionId/trace parameter。
- do not assume: 不得按显示名、拓扑位置或 action name 推断跨系统身份等价。

## gap_host_process_agent_depth: 主机/进程/Agent 深度不足

- 已知事实：Trace/detail 和 instance 相关响应出现 instance/agent 版本候选字段。
- 缺失证据：缺少主机、进程、Agent 的完整列表、稳定 ID 和归属关系。
- 对能力影响：资源拓扑矩阵只能 PARTIALLY_VERIFIED。
- 下一次 Capture 要补什么：Capture 实例详情、环境信息、Agent 版本页面和主机进程列表。
- 成功判定条件：证明 application instance -> host/process/agent 的字段血缘。
- 禁止假设：不得把 instanceName 或 IP 字符串直接当稳定主机 ID。
- related_capabilities:
  - `read_application_overview`
  - `get_trace_agent_context`
- related_endpoints:
  - `ep_post_server_api_graph_information`
  - `ep_post_server_api_action_trace_detail_queryagentversioninfo`
- related_recipes:
  - `scan_business_system`
  - `trace_investigation`
- evidence_seed: 从应用概览实例列表与 trace agent context 补充请求对比 instanceId / agent version 字段。

validation task:
- goal: 主机/进程/Agent 深度不足
- starting context: `read_application_overview` 与 `get_trace_agent_context`，重点看 `ep_post_server_api_graph_information` 和 `ep_post_server_api_action_trace_detail_queryagentversioninfo`。
- exploration target: Capture 实例详情、环境信息、Agent 版本页面和主机进程列表。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 证明 application instance -> host/process/agent 的字段血缘。
- do not assume: 不得把 instanceName 或 IP 字符串直接当稳定主机 ID。

## gap_container_pod_namespace: 容器 / Pod / Namespace 未发现

- 已知事实：Session 和导出中未发现 Kubernetes/容器相关非空证据。
- 缺失证据：缺少容器、Pod、Namespace endpoint 或响应字段。
- 对能力影响：该分支为 NOT_FOUND。
- 下一次 Capture 要补什么：在有容器化应用的环境重新抓取应用实例、拓扑和基础设施视图。
- 成功判定条件：出现可复核的 container/pod/namespace 字段或接口。
- 禁止假设：不得从应用名推断容器部署。

validation task:
- goal: 容器 / Pod / Namespace 未发现
- starting context: 使用本轮 `research/protocol/endpoint-contracts.yaml` 中相关 Endpoint。
- exploration target: 在有容器化应用的环境重新抓取应用实例、拓扑和基础设施视图。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 出现可复核的 container/pod/namespace 字段或接口。
- do not assume: 不得从应用名推断容器部署。

## gap_live_evidence_handoff_audit: live evidence handoff 可审计性不足

- 已知事实：`/Users/wangrundong/Downloads/live.zip` 已安全解压到临时目录并只读审计；包含 `preflight.json`、`request-log.jsonl`、`live-run-summary.json`、`final-report.md` 与 `LIVE-001..007-response.json`。
- 已确认：request count 一致，`request-log.jsonl` 7 条、raw response 7 个、summary requests 7 条，`final-report.md` 解释 LIVE-001..LIVE-007，编号连续。
- 状态冲突：`LIVE-002-response.json` business `code=INTERNAL`；`request-log.jsonl` 与 `live-run-summary.json` 将 LIVE-002 写成 `SUCCESS`，`final-report.md` 的 Request Audit 写成 INTERNAL error。应以 transport/business/result 三段状态修正。
- fingerprint 冲突：`live-run-summary.json` 的 business-system fingerprint 与 preflight raw business-system id 按当前 SHA-256 前 12 位规则一致；`final-report.md` 写为另一个 business-system fingerprint。application fingerprint 在 preflight/summary/final-report 之间一致。
- sanitization 冲突：`preflight.json` 保存真实业务系统名、应用名、bizSystemId、applicationId；`request-log.jsonl` 与 `live-run-summary.json` 的 `parameter_sources` 泄漏真实 `bizSystemId` / `applicationId`。`final-report.md` 未发现这些 raw id/name/IP/authorization 字符串。
- corrected sanitized handoff：已在 gitignored `research/sources/live/20260707-0200-business-system-vertical-slice/sanitized/` 生成修正版 `preflight.json`、`request-log.jsonl`、`live-run-summary.json`、`final-report.md`；`LIVE-002` JSON status 改为 FAILED，business-system fingerprint 统一，raw target identity 已移除。
- 缺失证据：zip 中没有 `LIVE-xxx-request.json`，因此 exact live request body、字段 presence 与部分 scope 判断仍不可审计。
- 时间语义：`request-log.jsonl` 记录 observed interval 17.0s；`preflight.json` 只有 `request_budget.min_interval_seconds=15`，`run_end_time_epoch_ms=null`，因此统一 RUN_END_TIME 只能视为 reported parameter source，不能视为已持久化证明。
- 对能力影响：上一轮 live lineage 可作为已记录协议事实保留；sanitized handoff status/fingerprint/sanitization 已有 local-only 修正版，但 RUN_END_TIME persistence 与 request evidence schema 仍需下一轮修正后才能完整审计 request shape。
- 下一次 Capture 要补什么：交付 local-only raw evidence 目录或 sanitized handoff；每个请求必须成对保存 request/response，并区分 transport_status、business_status、result。
- 成功判定条件：JSON handoff 中 INTERNAL 不再写成整体 SUCCESS；同一 raw identity 产生同一 fingerprint；sanitized 文件不包含真实 id/name/IP/credential；RUN_END_TIME 非 null 且持久化。
- 禁止假设：不得从 final-report 摘要反推出缺失 request body；不得伪造 request evidence 或改写 raw response。

validation task:
- goal: 修正 live evidence handoff v1，使下一轮可被离线审计。
- starting context: `research/sources/README.md` 的 Live evidence 本地约定。
- exploration target: 当前 handoff schema 的下一版产出 `preflight.json`、`request-log.jsonl`、`live-run-summary.json`、`final-report.md`、`LIVE-xxx-request.json`、`LIVE-xxx-response.json`。
- evidence to capture: sanitized request, sanitized response, timestamp, transport_status, business_status, result, fingerprint inputs/outputs, RUN_END_TIME.
- success criteria: request count、编号、状态、fingerprint、sanitization、interval 与 RUN_END_TIME 均可从文件复核。
- do not assume: 不得把 configured sleep 当 observed interval；不得把 null RUN_END_TIME 写成已证明统一时间锚点。

## gap_runtime_to_trace_list: transaction/actionItemList actionId 冷启动来源未证明

- 已知事实：`list_recent_requests` / `responseList` -> `trace/detail` -> `callTree` 已由 `live_evidence_round_2_2026-07-07` 证明，不再属于本 Gap。`actionItemList` 在缺少 `actionId` 参数时返回 INTERNAL，说明 transaction/actionItemList 路径仍需要前置 `actionId`。
- 缺失证据：Application / transaction context 如何获得 `actionItemList` 所需的冷启动 `actionId` 尚未证明；可能来自 URL、页面状态、前置请求或其他 observed READ response，但当前协议不能假设来源。
- 对能力影响：`alarm_to_trace` 中通过 transaction/actionItemList 枚举 Trace 的路径仍为 PARTIALLY_VERIFIED；`list_recent_requests` -> Trace 子路径已升级为 VERIFIED。
- live_evidence_round_1 (2026-07-07): PARTIAL — 4 次只读请求；确认 `actionItemList` 缺少 `actionId` 时失败，`responseList` 无需 `actionId` 但当时目标业务系统无活跃数据。Raw evidence local-only on validation host; durable migration pending。
- 下一次 Capture 要补什么：从 Application / transaction UI 冷启动进入 `actionItemList`，抓取 `actionId` 的来源（URL 参数、页面状态、前置请求或其他 observed READ response），再进入 Trace。
- 成功判定条件：证明 `actionItemList` request `actionId` 的上游来源，并证明该路径如何继续进入 trace detail request parameter。
- 禁止假设：不得用相似 actionId 补 traceGuid；不得把 `responseList.content[].actionId` 的成功样本泛化为 transaction/actionItemList 的冷启动来源。
- related_capabilities:
  - `resolve_action_context`
  - `list_transactions`
  - `get_trace_detail`
- related_endpoints:
  - `ep_get_server_api_action_get_12489`
  - `ep_get_server_api_action_alias_12489`
  - `ep_post_server_api_webaction_list_actionitemlist`
  - `ep_post_server_api_action_trace_detail`
- related_recipes:
  - `alarm_to_trace`
  - `trace_investigation`
- evidence_seed: `03-alarm-to-trace` request-0380/request-0381 for action context and request-0476/request-0490 for trace detail/callTree.

validation task:
- goal: 证明 transaction/actionItemList 的冷启动 `actionId` 来源。
- starting context: `resolve_action_context` 与 `list_transactions` (actionItemList)；`list_recent_requests` (responseList) -> `get_trace_detail` -> `get_trace_call_tree` 已 VERIFIED，仅作为已排除路径。
- exploration target: 在 UI 中从 Application / transaction context 进入 webaction/actionItemList，抓取 actionId 的 UI 来源。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 证明 actionItemList 的 actionId 参数来源（URL/前置请求/页面状态/其他 observed READ response）。
- do not assume: 不得用相似 actionId 补 traceGuid。
- round_1_finding: `actionItemList` 的 `actionId` 参数为必需项（省略返回 INTERNAL），冷启动无法获得。

## gap_application_charts_response_scope_shape: application/charts/response 空 series 的 scope/request-shape 未证明

- 已知事实：历史 Session 中 `ep_post_server_api_application_charts_response#variant_default` 成功返回非空 `data.series`，成功 request shape 为 form body `bizSystemId`, `businessType=BIZ_SYSTEM`, `timePeriod`, `endTime`, `lang`。同一类业务系统运行窗口下，`responseList` 可返回非空摘要项并可进入 Trace。
- 缺失证据：上一轮 live `application/charts/response` 返回业务成功但 `series=[]`；`request-log.jsonl` 只说明使用 target `bizSystemId`、`RUN_END_TIME`、`timePeriod=30` 和 “businessType determined by trial”。由于缺少 `LIVE-004-request.json`，无法确认最终 body、`businessType` 具体值、是否还存在其他 scope/shape 字段差异。
- 对能力影响：不能把空 series 简化为“无流量”；必须保留 scope mismatch、request-shape mismatch、field presence mismatch、time anchor mismatch 和 `businessType` 语义未解。
- businessType 审计：历史成功 shape 总是包含 `businessType=BIZ_SYSTEM`。live request-log 提到 businessType 由 trial 决定，但无 request file 证明具体值；因此仍不能证明 `businessType` 语义上 optional。
- 下一次 Capture 要补什么：只验证一个 historical scope/request-shape 差异，不做 applicationId/applicationIds/bizSystemId/businessType 组合扫描。
- 成功判定条件：在同一 target business-system fingerprint 与固定 RUN_END_TIME 下，使用 historical successful shape 得到可解释的 business_status 和 series 结果。
- 禁止假设：不得用 responseList 非空直接证明 application/charts/response scope 正确；不得把空 series 写成 no traffic。
- related_capabilities:
  - `read_performance_timeseries`
  - `list_recent_requests`
- related_endpoints:
  - `ep_post_server_api_application_charts_response`
  - `ep_post_server_api_webaction_list_responselist`
- related_recipes:
  - `scan_business_system`

Micro Experiment B:
- goal: 验证 `application/charts/response` live empty series 是否由 historical business-system scope/request-shape 差异导致。
- exact endpoint id: `ep_post_server_api_application_charts_response`
- exact variant id: `variant_default`
- target application scope: use the target application only to identify its parent business-system fingerprint; request shape remains the historical business-system scope because this variant has no observed `applicationId`/`applicationIds`.
- fixed time anchor: persisted non-null `RUN_END_TIME` with ISO8601 and epoch ms.
- single request shape to validate: `POST /server-api/application/charts/response` form body `bizSystemId=<parent target>`, `businessType=BIZ_SYSTEM`, `timePeriod=<fixed>`, `endTime=<RUN_END_TIME>`, `lang=zh_CN`.
- maximum requests: 1.
- stop conditions: stop after the first response; record whether `data.series` is non-empty, empty, or absent, with transport_status/business_status/result and sanitized request/response.

## gap_stack_non_empty: Stack 非空结构未充分证明

- 已知事实：`detail/stackTraces` endpoint 被观察到；Trace Detail response 中也已观察到 embedded exception evidence，且 `data.exceptions[].stack[]` / `data.timeLine.subTimeLines[].errors[].stack[]` 在部分历史 Session 中非空。
- 缺失证据：代表性非空 `detail/stackTraces` endpoint item 字段覆盖不足。
- 对能力影响：Stack 分支只能 PARTIALLY_VERIFIED。
- 下一次 Capture 要补什么：选择含异常栈的 trace，抓取 stackTraces 非空响应。
- 成功判定条件：获得非空 stack frame 字段并关联 treeId/traceId。
- 禁止假设：不得从 exception msg 构造 stack。
- related_capabilities:
  - `get_trace_stack`
  - `list_trace_exceptions`
- related_endpoints:
  - `ep_post_server_api_action_trace_detail_stacktraces`
  - `ep_post_server_api_action_trace_detail_exceptions`
- related_recipes:
  - `trace_investigation`
- evidence_seed: 从已知异常 Trace 先抓 exceptions，再抓 stackTraces 非空响应；Trace Detail embedded stack evidence 可作为候选线索，但不替代独立 stackTraces endpoint。

validation task:
- goal: Stack 非空结构未充分证明
- starting context: `list_trace_exceptions` -> `get_trace_stack`，重点看 exceptions 与 stackTraces 的共同 trace context。
- exploration target: 选择含异常栈的 trace，抓取 stackTraces 非空响应。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 获得非空 stack frame 字段并关联 treeId/traceId。
- do not assume: 不得从 exception msg 构造 stack。

## gap_database_nosql_mq_metrics: 数据库/NoSQL/MQ 指标深度不均

- 已知事实：Session 有数据库/NoSQL/外部服务部分 endpoint，MQ 多为文档。
- 缺失证据：缺少三类组件相同深度的 list/chart/trace 字段观察并集。
- 对能力影响：组件性能矩阵为 PARTIALLY_VERIFIED。
- 下一次 Capture 要补什么：分别选择数据库、Redis/NoSQL、MQ 调用边并进入列表、图表、Trace。
- 成功判定条件：每类至少一个非空 list、chart、trace 响应。
- 禁止假设：不得把 NoSQL 字段套用到 MQ。
- related_capabilities:
  - `list_component_operations`
- related_endpoints:
  - `ep_post_server_api_component_database_actionlist`
  - `ep_post_server_api_nosql_componentname_list`
  - `ep_post_server_api_mq_mqapplication_list`
  - `ep_post_server_api_mq_consume_product`
- related_recipes:
  - `scan_business_system`
- evidence_seed: 分别从数据库 actionList、NoSQL componentName/list、MQ documented endpoints 找同深度非空 list/chart/trace。

validation task:
- goal: 数据库/NoSQL/MQ 指标深度不均
- starting context: `list_component_operations`，重点看 database actionList、NoSQL componentName/list、MQApplication/list 与 consume-product。
- exploration target: 分别选择数据库、Redis/NoSQL、MQ 调用边并进入列表、图表、Trace。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 每类至少一个非空 list、chart、trace 响应。
- do not assume: 不得把 NoSQL 字段套用到 MQ。

## gap_doc_observed_prefix_conflicts: 官方文档与 Session path 前缀存在冲突

- 已知事实：文档出现 `/server-config/...`、`/alarm-api/...`，Session 常见 `/server-api/...`、`/nalarm-api/...`。
- 缺失证据：缺少同一环境对文档路径的 live 证明；本轮禁止 live request。
- 对能力影响：不能声明 fallback/equivalent。
- 下一次 Capture 要补什么：未来只读测试环境中对 documented-only 路径做 HEAD/OPTIONS/只读 POST 验证，或抓取 UI 调用。
- 成功判定条件：确认 exact path 可用、不可用或版本差异。
- 禁止假设：不得自动把 `alarm-api` 改写成 `nalarm-api`。

validation task:
- goal: 官方文档与 Session path 前缀存在冲突
- starting context: 使用本轮 `research/protocol/endpoint-contracts.yaml` 中相关 Endpoint。
- exploration target: 未来只读测试环境中对 documented-only 路径做 HEAD/OPTIONS/只读 POST 验证，或抓取 UI 调用。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 确认 exact path 可用、不可用或版本差异。
- do not assume: 不得自动把 `alarm-api` 改写成 `nalarm-api`。

## gap_export_sort_filter_semantics: 导出列不能证明服务端排序过滤

- 已知事实：导出含 P99、吞吐率、错误率等列。
- 缺失证据：没有对应 `sortField/filter` 请求证据。
- 对能力影响：normalized_mapping 只标 display_only。
- 下一次 Capture 要补什么：在 UI 中对 P99/错误率排序或过滤并抓取请求。
- 成功判定条件：观察到真实 sort/filter 参数与响应顺序变化。
- 禁止假设：不得根据 CSV 列名猜 `sortField=p99`。

validation task:
- goal: 导出列不能证明服务端排序过滤
- starting context: 使用本轮 `research/protocol/endpoint-contracts.yaml` 中相关 Endpoint。
- exploration target: 在 UI 中对 P99/错误率排序或过滤并抓取请求。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 观察到真实 sort/filter 参数与响应顺序变化。
- do not assume: 不得根据 CSV 列名猜 `sortField=p99`。

## gap_write_readback_completeness: 部分写能力回读/恢复链路不完整

- 已知事实：告警 CRUD、异常检测、配置保存均有真实写请求；部分有回读或恢复。
- 缺失证据：并非每个写 endpoint 都有完整 save -> readback -> restore 证据。
- 对能力影响：写能力保存为协议资料，不升级为自动执行 Recipe。
- 下一次 Capture 要补什么：对每个写对象捕获前置读取、最小修改、回读验证、恢复、最终回读。
- 成功判定条件：每个动态 ID 和恢复 payload 均有证据。
- 禁止假设：不得设计 dry-run/rollback 执行框架。
- related_capabilities:
  - `manage_business_settings`
  - `manage_alarm_rules`
  - `manage_anomaly_detection_policy`
- related_endpoints:
  - `ep_post_server_api_data_business_updatebizsystemsetting`
  - `ep_post_nalarm_api_config_setting_save`
  - `ep_post_nalarm_api_config_setting_update_policys`
- evidence_seed: 写能力仅作为 Endpoint Contract 与 Capability 证据保留，不再建正式 Recipe。

validation task:
- goal: 部分写能力回读/恢复链路不完整
- starting context: `manage_business_settings`、`manage_alarm_rules`、`manage_anomaly_detection_policy` 的读写/回读端点。
- exploration target: 对每个写对象捕获前置读取、最小修改、回读验证、恢复、最终回读。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 每个动态 ID 和恢复 payload 均有证据。
- do not assume: 不得设计 dry-run/rollback 执行框架。
