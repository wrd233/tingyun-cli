# Catalog Coverage Report

Generated from the provided PDF text layer. This report is intentionally concise so agents can diff it across catalog regenerations.

- Source PDF: `/Users/wangrundong/Downloads/基调听云应用与微服务API说明.pdf`
- Product version: `V3.9.0.0`
- Manual version: `V1.07`
- Endpoint candidates from PDF: `274`
- Catalog endpoints including auth: `275`

## Safety Counts

- `guarded`: `3`
- `read`: `193`
- `unknown`: `4`
- `write`: `75`

## Domain Counts

- `application`: `82`
- `auth`: `1`
- `background_task`: `8`
- `business_system`: `34`
- `component`: `22`
- `config`: `75`
- `diagnosis`: `1`
- `error`: `16`
- `health_rule`: `5`
- `service_interface`: `12`
- `trace`: `2`
- `transaction`: `17`

## Confidence Counts

- `high`: `177`
- `low`: `62`
- `medium`: `36`

## Low Confidence Endpoints

- `business_system.2_3_2_8_2_1.database_analysis` `POST /server-api/{Database}/analysis` - 调用列表
- `business_system.2_3_2_9_1_1.component_chart_resptime` `POST /server-api/component/chart/respTime` - 执行时间
- `business_system.2_3_2_9_2.errorlist` `POST /server-api/errorList` - 异常
- `application.3_1_1.application_app_list` `POST /server-api/application/app/list` - 应用实例
- `application.3_2_2.application_business_systemconflist` `POST /server-api/application/business/systemConfList` - 业务系统下拉列表
- `application.3_2_4_4.api_event_getwarnandcriticalcounts` `POST /alarm-api/api/event/getWarnAndCriticalCounts` - 应用警告
- `application.3_2_4_5.application_charts_response` `POST /server-api/application/charts/response` - 响应时间
- `application.3_2_4_6.application_charts_throught` `POST /server-api/application/charts/throught` - 吞吐率
- `application.3_2_4_7.application_charts_error` `POST /server-api/application/charts/error` - 错误率
- `application.3_2_5_1.application_charts_error` `POST /server-api/application/charts/error` - 错误率
- `application.3_2_14_1.application_appicationid_aciveinstanceinfo` `POST /server-api/application/{appicationId}/aciveInstanceInfo` - 活跃实例列表
- `application.4_9_1.graph_query_overview_application_service_flow` `POST /server-api/graph/query/overview?application_service_flow` - 应用 ServiceFlow
- `application.4_9_2.graph_query_overview_application_request_service_flow` `POST /server-api/graph/query/overview?application_request_service_flow` - ServiceFlow 请求列表
- `application.4_9_3.graph_query_overview_application_instance_service_flow` `POST /server-api/graph/query/overview?application_instance_service_flow` - ServiceFlow 实例列表
- `transaction.5_2_1_4.errortop10` `POST /server-api/errorTop10` - Top10 错误
- `transaction.5_2_1_7.health_simpletrace` `POST /server-api/health/simpleTrace` - 健康度
- `transaction.5_2_2_1.webaction_charts_error` `POST /server-api/webaction/charts/error` - 错误率
- `transaction.5_2_2_3.errortop10` `POST /server-api/errorTop10` - Top10 错误
- `transaction.5_2_2_4.errorlist` `POST /server-api/errorList` - 错误列表
- `transaction.5_2_4_1.action_trace` `POST /server-api/action/trace` - 事务追踪
- `service_interface.6_2_2_1.webaction_charts_error` `POST /server-api/webaction/charts/error` - 错误率
- `service_interface.6_2_2_2.webaction_charts_response_quantlie` `POST /server-api/webaction/charts/response-quantlie` - 响应时间
- `service_interface.6_2_2_3.webaction_charts_throught` `POST /server-api/webaction/charts/throught` - 吞吐率
- `service_interface.6_2_2_4.component_performancedecompose_list` `POST /server-api/component/performanceDecompose/list` - 性能分解列表
- `service_interface.6_2_2_5.component_chart_performancedecompose` `POST /server-api/component/chart/performanceDecompose` - 性能分解图表
- `service_interface.6_2_2_6.health_simpletrace` `POST /server-api/health/simpleTrace` - 健康度
- `service_interface.6_2_3_1.webaction_charts_error` `POST /server-api/webaction/charts/error` - 错误率
- `service_interface.6_2_3_2.errortop10` `POST /server-api/errorTop10` - Top10 错误
- `service_interface.6_2_3_3.errorlist` `POST /server-api/errorList` - 错误列表
- `service_interface.6_2_3_3.action_trace` `POST /server-api/action/trace` - 服务接口追踪
- `background_task.7_2_1_1.graph_queryactiongraph` `POST /server-api/graph/queryActionGraph` - 后台任务拓扑
- `background_task.7_2_1_2.webaction_charts_error` `POST /server-api/webaction/charts/error` - 错误率
- `background_task.7_2_1_3.webaction_charts_response_quantlie` `POST /server-api/webaction/charts/response-quantlie` - 响应时间
- `background_task.7_2_1_4.webaction_charts_throught` `POST /server-api/webaction/charts/throught` - 吞吐率
- `background_task.7_2_2_1.webaction_charts_error` `POST /server-api/webaction/charts/error` - 错误率
- `background_task.7_2_2_2.errortop10` `POST /server-api/errorTop10` - Top10 错误
- `background_task.7_2_2_3.errorlist` `POST /server-api/errorList` - 错误列表
- `component.8_1_1_1.action_trace` `POST /server-api/action/trace` - 后台任务追踪
- `component.8_1_1_1_1.component_database_errorlist` `POST /server-api/component/database/errorList` - 接口 URL
- `component.8_1_2_1_1.component_database_actionlist` `POST /server-api/component/database/actionList` - 接口 URL
- `component.8_1_3_1_1.database_operate_analysislist` `POST /server-api/Database/operate/analysisList` - 接口 URL
- `component.8_1_4_1_1.component_database_actiontracelist` `POST /server-api/component/database/actionTraceList` - 接口 URL
- `component.8_1_5_1_1.component_database_actionlist` `POST /server-api/component/database/actionList` - 接口 URL
- `component.8_1_6_1_1.database_analysis` `POST /server-api/Database/analysis` - 接口 URL
- `component.8_1_7_1.component_database_erroractiontracelist` `POST /server-api/component/database/errorActionTraceList` - 错误 TOP100 追踪列表接口 URL
- `component.8_1_8_1.rootcauseerrorlist` `POST /server-api/rootCauseErrorList` - 错误 Root cause 列表接口 URL
- `component.8_1_9_1_1.sqlerrorlist` `POST /server-api/sqlErrorList` - 接口 URL
- `component.8_1_10_1_1.component_database_errordataitem` `POST /server-api/component/database/errorDataItem` - 接口 URL
- `component.8_1_11_1_1.component_database_errorlist` `POST /server-api/component/database/errorList` - 接口 URL
- `component.8_1_12_1_1.component_database_actiontracelist` `POST /server-api/component/database/actionTraceList` - 接口 URL
- `component.8_1_13_1_1.component_database_actiontracelist` `POST /server-api/component/database/actionTraceList` - 接口 URL
- `component.8_1_14_1_1.graph_component_querydatabasegraph` `POST /server-api/graph/component/queryDataBaseGraph` - 接口 URL
- `component.8_1_15_1_1.database_list` `POST /server-api/Database/list` - 接口 URL
- `component.8_3_1_1.component_chart_throughput` `POST /server-api/component/chart/throughput` - 吞吐率
- `component.8_3_1_2.component_chart_resptime` `POST /server-api/component/chart/respTime` - 执行时间
- `error.9_1_2.errorlist` `POST /server-api/errorList` - 错误列表
- `error.10_12.error_smart_errorexport_creattask` `POST /server-api/error/smart/errorExport/creatTask` - 创建错误异常列表导出任务
- `trace.11_1.action_trace` `POST /server-api/action/trace` - 事务追踪列表
- `config.12_2_3_13.config_dataitem_init_classname` `POST /server-config/config/dataitem/init/classname` - 搜索方法参数 Class 列表
- `config.12_2_6_10.data_application_list` `POST /server-config/data/application/list` - 应用下拉框
- `config.12_2_6_14.data_business_applicationsetting_savaembeddecodeinf` `POST /server-config/data/business/applicationSetting/savaEmbeddeCodeInf` - 新增/修改自定义嵌码
- `config.12_3_4_2_4.data_business_applicationsetting_creatorupdateactiont` `POST /server-config/data/business/applicationSetting/creatOrUpdateActionT` - 配置事务追踪

## Notes

- Duplicate paths are retained when the PDF presents them in different sections or contexts.
- The catalog stores short evidence excerpts, page numbers, and extracted table rows, not a full PDF transcript.
- `guarded`, `write`, and `unknown` entries are cataloged for traceability but cannot be executed by the first-version CLI.
