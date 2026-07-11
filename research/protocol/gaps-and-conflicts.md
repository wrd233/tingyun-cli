# Gaps and Conflicts

本文件只记录未解决问题、冲突和未来 validation task。所有未知连接保留为 Gap，不在协议中补全。

Resolved note: Candidate Dataset Source Gate 已由真实 Session 证据关闭。v1 Primary Stable Candidate Source 是 `POST /server-api/graph/query/overview?request_overview`；Export / Download 保留为研究验证来源和未来 File-native Evidence Source，不作为 Runtime fallback。返回恰好 1000 行仍然不是 `FULL` 证明。

Integration note (2026-07-10): Core Collect 仍为 3 个逻辑请求。error/throughput series、alarm、recent request、instance、external 和 trace-exception 能力只通过一次一个的 Advanced Source READ recipe 进入；本次 integration 为 0 Live。responseList 的 Trace lineage 只适用于 response ranking，errorList/throughtList 仍不能继承。所有 WRITE/UNKNOWN 和 research-only path 继续排除在生产安全面之外。

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
- evidence_seed: 从 `01-business-system-top-down` 的业务系统拓扑请求开始，沿同一 UI 点击补齐下游请求。`20260707-0400-micro-shape-scope-validation` 已确认 `queryBizDetailGraph` 的完整可执行 shape：`mergeGraph="1"` 与 `cascadingDisplay="1"` 字符串值返回非空 topology；本 Gap 仅保留跨系统下游参数血缘，不再包含 topology 请求形态未解项。

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

## gap_live_evidence_handoff_audit: final preflight RUN_END_TIME 持久化不足

- 已知事实：`20260707-0400-micro-shape-scope-validation` 交付了 `LIVE-001/002-request.json` 与对应 response，`request-log.jsonl`、`sanitized/live-run-summary.json`、`sanitized/final-report.md` 均显示 status semantics `PASS`；fingerprint consistency、sanitization 与 request/response pairing 已满足本轮审计要求。
- 已确认：`run_end_time.txt` 保存 ISO8601 与 epoch ms；request evidence 的 `endTime` 与 `run_end_time_reference` 可复核，说明执行时实际使用了统一 RUN_END_TIME。
- 剩余缺口：`preflight.json` 仍保留 `run_end_time_iso8601=null` 与 `run_end_time_epoch_ms=null`。`preflight.json` 必须是执行前最终网络请求快照，不是模板；不能用后续 `run_end_time.txt` 反向证明 preflight 已冻结非 null 值。
- 对能力影响：micro run 可作为 endpoint request-shape 与 response-shape 证据；handoff schema 仍需修正 final preflight persistence，避免后续审计无法判断 LIVE-001 前的时间锚点冻结状态。
- 下一次 Capture 要补什么：按顺序生成并冻结 handoff：confirm experiment -> generate RUN_END_TIME -> persist into `preflight.json` -> freeze preflight -> execute LIVE-001。
- 成功判定条件：`preflight.json`、`run_end_time.txt`、每个 `LIVE-xxx-request.json` 与 summary 中的 RUN_END_TIME 一致且非 null；request/response 成对保存；状态继续区分 `transport_status`、`business_status` 与 `result`。
- 禁止假设：不得把 null preflight 当作模板后补；不得从后续 summary 或 request 文件反推 preflight 已合规。

validation task:
- goal: 修正 live evidence handoff preflight，使下一轮可证明 LIVE-001 前 RUN_END_TIME 已持久化。
- starting context: `research/sources/README.md` 的 Live evidence 本地约定。
- exploration target: 当前 handoff schema 的下一版产出非 null final `preflight.json`、`run_end_time.txt`、`request-log.jsonl`、`live-run-summary.json`、`final-report.md`、`LIVE-xxx-request.json`、`LIVE-xxx-response.json`。
- evidence to capture: final preflight timestamp, sanitized request, sanitized response, transport_status, business_status, result, fingerprint inputs/outputs, RUN_END_TIME.
- success criteria: preflight、request、summary 与 run_end_time 文件中的 RUN_END_TIME 均非 null 且一致。
- do not assume: 不得把 null preflight 当作已冻结最终请求快照；不得把 configured sleep 当 observed interval。

## gap_runtime_to_trace_list: transaction/actionItemList actionId 冷启动来源未证明

- 已知事实：Core Golden Path 已通过 request_overview Candidate -> `trace/detail` -> `callTree` 验证；v1.1 resolver 只接受 Web+WEB -> WEB、Web+TX -> TX、Background+BG -> BG、Web+TX,IF -> TX。`list_recent_requests` / `responseList` -> `trace/detail` -> `callTree` 也已由 `live_evidence_round_2_2026-07-07` 证明，现在只通过正式 Advanced Source response-ranking recipe 进入，不属于 Core；`actionItemList` 仍需要前置 `actionId`。
- 缺失证据：Application / transaction context 如何获得 `actionItemList` 所需的冷启动 `actionId` 尚未证明；可能来自 URL、页面状态、前置请求或其他 observed READ response，但当前协议不能假设来源。
- 对能力影响：不影响 v1 Golden Path；`alarm_to_trace` 中通过 transaction/actionItemList 枚举 Trace 的路径仍为 PARTIALLY_VERIFIED；`list_recent_requests` -> Trace 子路径已升级为 VERIFIED。
- live_evidence_round_1 (2026-07-07): PARTIAL — 4 次只读请求；确认 `actionItemList` 缺少 `actionId` 时失败，`responseList` 无需 `actionId` 但当时目标业务系统无活跃数据。Raw evidence local-only on validation host; durable migration pending。
- 下一次 Capture 要补什么：从 Application / transaction UI 冷启动进入 `actionItemList`，抓取 `actionId` 的来源（URL 参数、页面状态、前置请求或其他 observed READ response），再进入 Trace。
- 成功判定条件：证明 `actionItemList` request `actionId` 的上游来源，并证明该路径如何继续进入 trace detail request parameter。
- 禁止假设：不得用相似 actionId 补 traceGuid；不得把 request_overview Candidate 或 `responseList.content[].actionId` 的成功样本泛化为 transaction/actionItemList 的冷启动来源。
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
- starting context: `resolve_action_context` 与 `list_transactions` (actionItemList)；v1 request_overview Candidate -> Trace 和 `list_recent_requests` (responseList) -> Trace 均已 VERIFIED，仅作为已排除路径。
- exploration target: 在 UI 中从 Application / transaction context 进入 webaction/actionItemList，抓取 actionId 的 UI 来源。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 证明 actionItemList 的 actionId 参数来源（URL/前置请求/页面状态/其他 observed READ response）。
- do not assume: 不得用相似 actionId 补 traceGuid。
- round_1_finding: `actionItemList` 的 `actionId` 参数为必需项（省略返回 INTERNAL），冷启动无法获得。

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
- 对能力影响：导出列仍不能反推服务端排序/过滤参数；这不影响 request_overview List API 作为 v1 Candidate Dataset 主来源。
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
## gap_dubbo_provider_trace_action_type: DubboProvider TX,IF direct Trace actionType 未证明

- 已知事实：Web transaction + `TX,IF` 使用 `actionType=TX` 有成功 Trace 证据；私有七日证据中 DubboProvider + `TX,IF` 沿用 TX 时失败，Call Tree 内 Dubbo span 可显示 IF。
- 缺失证据：同一 DubboProvider Candidate 对 direct `actionType=IF` 的受控只读成功样本。
- 对能力影响：`DUBBO_PROVIDER_INTERFACE + TX,IF` 返回 `UNRESOLVED_TRACE_ACTION_TYPE`，不暴露 `investigate_trace`；建议从已验证 parent Web transaction 进入 Trace/Call Tree，但不自动执行。
- 下一次 Capture 要补什么：在具备凭据和 exact historical Candidate 时，串行执行至多一个 `actionType=IF` focused READ 请求并保存 request/response lineage。
- 成功判定条件：同一 Candidate exact identity 返回 target-correct Trace，且无 WRITE/UNKNOWN endpoint。
- 禁止假设：不得把 Web TX 证明、Call Tree 的 IF 标签或 composite 字符串拆分当作 direct Dubbo Trace 证明。
- related_capabilities:
  - `normalize_candidate_semantics`
  - `get_trace_detail`
- related_endpoints:
  - `ep_post_server_api_action_trace_detail`
- related_recipes:
  - `alarm_driven_investigation_reliability`

## gap_application_instances_http_500: application-instances 同形请求 HTTP 500

- 已知事实：Observed 请求是 POST `/server-api/graph/information` form body，字段为 `bizSystemId/applicationId/timePeriod/endTime/lang`；当前 CLI request shape 与其完全一致。该请求返回 HTTP 500。
- 缺失证据：不存在一个有证据支持的修正字段、scope、endpoint 或 body kind，也没有当前可用只读凭据。
- 对能力影响：实例 Source 的 Live 合同保持 unresolved；HTTP 500 不能解释为无实例、无指标或权限不足。离线 normalization 和 composition 仍可验证。
- 下一次 Capture 要补什么：先从浏览器成功实例页获取同环境 exact request contract；只有合同出现明确差异后才执行一次 focused READ。
- 成功判定条件：修正合同得到非错误业务响应并保存 instance item shape。
- 禁止假设：不得重复相同失败请求，不得更换未证明 endpoint，不得从 HTTP 500 推断空数据或权限原因。
- related_capabilities:
  - `read_application_overview`
- related_endpoints:
  - `ep_post_server_api_graph_information`
- related_recipes:
  - `alarm_driven_investigation_reliability`
