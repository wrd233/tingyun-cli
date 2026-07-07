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

## gap_runtime_to_trace_list: 运行对象到 Trace 列表血缘不完整

- 已知事实：已观察 webaction/external/error 清单和 trace detail。
- 缺失证据：部分运行清单 item 到 `traceGuid/actionGuid/queryTimestamp` 的来源未完整闭环。`list_transactions` (actionItemList) 路径仍缺 actionId 冷启动来源。
- 对能力影响：alarm_to_trace 以 PARTIALLY_VERIFIED 表示；`list_recent_requests` → trace 子路径已升级为 VERIFIED。
- live_evidence_round_1 (2026-07-07): PARTIAL — 4 次只读请求，目标业务系统无活跃数据。
  - 已确认：`getBusinessTree` → `bizSystemId` + `applicationId` 链路正常可用。
  - 已确认：`actionItemList` 在缺少 `actionId` 参数时返回 INTERNAL 错误（该参数为必需项）。
  - 已确认：`responseList`（list_recent_requests）无需 `actionId` 即可调用，但目标业务系统在 120 分钟窗口内返回空列表。
  - evidence_ref: `/tmp/tingyun-evidence/live_live_001..004_response.json` (本地，未提交)
- live_evidence_round_2 (2026-07-07): PASS — `list_recent_requests` → trace/detail → callTree 完整血缘已证明（5 次只读请求，EDI 业务系统）。
  - **已证明血缘链：**
    1. `responseList.content[].actionId` → `trace/detail` request `actionId` (exact match)
    2. `trace/detail` response `actionGuid` → `callTree` request `actionGuid` (exact match)
    3. `trace/detail` response `id` → `callTree` request `traceId` (exact match)
  - **新发现：** `trace/detail` 可以用 `actionId`（无需 `actionGuid`）调用；响应中 `actionGuid == traceGuid`。
  - **新发现：** `trace/detail` 响应中 `data.id` 即为 `traceId`，用于 callTree。
  - **仍阻塞：** `actionItemList` (list_transactions) 需要 `actionId`，冷启动无法获得；`action/get` 和 `action/alias` 不返回 `actionGuid`。
  - evidence_ref: `/tmp/tingyun-evidence/round2_live_001..005_response.json` (本地，未提交)
- 下一次 Capture 要补什么：在 UI 中从事务列表 (actionItemList) 点击进入 Trace，抓取 actionId 的 UI 来源（URL参数/页面状态/前置请求），补全 `list_transactions` → trace 的最后一段。
- 成功判定条件：证明 list.response.field -> trace detail request.parameter。
- 禁止假设：不得用相似 actionId 补 traceGuid。
- related_capabilities:
  - `resolve_action_context`
  - `list_transactions`
  - `list_recent_requests`
  - `get_trace_detail`
  - `get_trace_call_tree`
- related_endpoints:
  - `ep_get_server_api_action_get_12489`
  - `ep_get_server_api_action_alias_12489`
  - `ep_post_server_api_webaction_list_actionitemlist`
  - `ep_post_server_api_webaction_list_responselist`
  - `ep_post_server_api_action_trace_detail`
  - `ep_post_server_api_action_trace_calltree`
- related_recipes:
  - `alarm_to_trace`
  - `trace_investigation`
- evidence_seed: `03-alarm-to-trace` request-0380/request-0381 for action context and request-0476/request-0490 for trace detail/callTree.

validation task:
- goal: 运行对象到 Trace 列表血缘不完整 — `list_recent_requests` 路径已闭环，`list_transactions` (actionItemList) 路径仍需 actionId 冷启动来源。
- starting context: `list_recent_requests` (responseList) -> `get_trace_detail` -> `get_trace_call_tree` 已 VERIFIED；`resolve_action_context` -> `list_transactions` (actionItemList) 仍缺 actionId 来源。
- exploration target: 在 UI 中从 webaction/actionItemList 页面点击进入 Trace，抓取 actionId 的 UI 来源。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 证明 actionItemList 的 actionId 参数来源（URL/前置请求/页面状态）。
- do not assume: 不得用相似 actionId 补 traceGuid。
- round_1_finding: `actionItemList` 的 `actionId` 参数为必需项（省略返回 INTERNAL），冷启动无法获得。`responseList` 在测试目标上返回空数据。
- round_2_finding: `responseList` → `trace/detail` → `callTree` 完整血缘已用 exact value match 证明；`trace/detail` 接受 `actionId` 作为唯一身份参数（无需 `actionGuid`）；响应中 `actionGuid == traceGuid`，`data.id` 即为 `traceId`。

## gap_recent_request_trace_selection: 近期请求清单到 Trace 选择需要补证

- 已知事实：导出和 Session 证明请求统计清单存在。
- 缺失证据：缺少近期清单中用户选择某一 item 后的 traceGuid 生成方式。
- 对能力影响：近期清单入口为 PARTIALLY_VERIFIED。
- 下一次 Capture 要补什么：Capture 业务系统近期请求清单，排序后点击一条进入 Trace。
- 成功判定条件：记录 item 字段、点击 URL、后续 request 参数。
- 禁止假设：不得把 CSV 事务名称当 Wire trace key。
- related_capabilities:
  - `list_recent_requests`
  - `get_trace_detail`
- related_endpoints:
  - `ep_post_server_api_webaction_list_responselist`
  - `ep_post_server_api_webaction_list_throughtlist`
  - `ep_post_server_api_webaction_list_errorlist`
  - `ep_post_server_api_action_trace_detail`
- related_recipes:
  - `scan_business_system`
- evidence_seed: 从 webaction response/throught/error list 的 item 字段点击进入 Trace，并保存页面 URL 与后续 trace/detail 请求。

validation task:
- goal: 近期请求清单到 Trace 选择需要补证
- starting context: `list_recent_requests`，重点看 responseList、throughtList、errorList 及后续 trace/detail。
- exploration target: Capture 业务系统近期请求清单，排序后点击一条进入 Trace。
- evidence to capture: request, response, page URL, journey interaction, export if produced.
- success criteria: 记录 item 字段、点击 URL、后续 request 参数。
- do not assume: 不得把 CSV 事务名称当 Wire trace key。

## gap_stack_non_empty: Stack 非空结构未充分证明

- 已知事实：`detail/stackTraces` endpoint 被观察到。
- 缺失证据：代表性非空 stack item 字段覆盖不足。
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
- evidence_seed: 从已知异常 Trace 先抓 exceptions，再抓 stackTraces 非空响应。

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
