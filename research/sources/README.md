# 听云协议研究来源登记
本目录保存本轮离线研究输入。`sessions/`、`official-docs/`、`exports/` 为真实源材料，默认不提交 Git；长期版本化目标仅为本 README 与 `research/protocol/`。

## Live evidence 本地约定

`research/sources/live/` 预留给运行验证机器上的 live evidence 原始材料，目录内容 local-only，不提交 Git。该目录不得保存 Authorization、Cookie、Token 或其他可用凭证；协议文件只引用稳定 run identity（例如 `live_evidence_round_2_2026-07-07`）和字段血缘摘要。若 raw evidence 不在当前 Codex workspace，不创建空文件或伪造迁移，只记录 raw evidence local-only on validation host / durable migration pending。

## Session ZIP 处理记录
| 整理目录 | 原始包名 | Session 名称 | Session ID | 文件数 | 处理状态 | SHA-256 |
|---|---:|---|---|---:|---|---|
| `01-business-system-top-down` | `ai-ready 5.zip` | 了解一个业务系统的拓扑(自顶向下) | `session-0ec41a62-cb8c-46bf-be25-bc46cfdc48b6` | 1132 | safe-extracted, readable, original ZIP removed | `642500bc18bc361e0b0cc792869480a57d47c62f449e597bf4cbdf14c6f33ed8` |
| `02-application-deep-dive` | `ai-ready 4.zip` | [应用]从一个应用界面入手 | `session-7b8e8a6f-5272-450c-93d6-0499264169b3` | 582 | safe-extracted, readable, original ZIP removed | `c5fd14fef016288d1a1b4f875aa09b164fa06decc2e8b317054072a5256193d5` |
| `03-alarm-to-trace` | `ai-ready 6.zip` | 查看告警并一路追踪 | `session-efc0742e-e170-4f55-a0de-e0f44e89bd6e` | 506 | safe-extracted, readable, original ZIP removed | `6602f62c3706b19d411ada57ec1eb3891d5f499aed8a646ea9fa73b15a32329b` |
| `04-configuration-management` | `ai-ready 2.zip` | [配置]配置管理 | `session-dfd40754-b596-496a-bd98-8cd433a00aa2` | 366 | safe-extracted, readable, original ZIP removed | `152a9e607438d952717476b5ae3991f7c066d45a23df1478b18dacfa4319f138` |
| `05-anomaly-detection` | `ai-ready 3.zip` | [异常检测] | `session-ffe75ef5-2c9b-46de-9718-63bf104cdb44` | 79 | safe-extracted, readable, original ZIP removed | `c9ca672a79c230e2975e3493f42946d484734205b12d1d8789af6cc4054dda4d` |
| `06-alarm-configuration` | `ai-ready.zip` | [告警配置] | `session-9a4c42b2-5e29-4e02-b01c-9891d718a710` | 278 | safe-extracted, readable, original ZIP removed | `0beae954803717e802c81a82818b2deaafc22667d3c2515508efc2e22d39c1a4` |

## Session 覆盖统计
| Session | 文件总数 | 已检查 | 协议研究使用 | 明确无协议价值或重复 | 无法识别 | 网络记录 |
|---|---:|---:|---:|---:|---:|---:|
| `01-business-system-top-down` | 1132 | 1132 | 1129 | 3 | 0 | 576 |
| `02-application-deep-dive` | 582 | 582 | 579 | 3 | 0 | 297 |
| `03-alarm-to-trace` | 506 | 506 | 501 | 5 | 0 | 266 |
| `04-configuration-management` | 366 | 366 | 363 | 3 | 0 | 180 |
| `05-anomaly-detection` | 79 | 79 | 76 | 3 | 0 | 37 |
| `06-alarm-configuration` | 278 | 278 | 275 | 3 | 0 | 137 |

合计：2943/2943 Session 文件已检查；1493/1493 网络记录已扫描；观察到 216 个去重 method + path，其中 202 个进入服务端协议候选总账，47 条静态/UI 记录仅进入覆盖统计。

## 官方文档
- `application-and-microservice-api.pdf`：172 个去重文档 Endpoint；SHA-256 `627ffedcf6ec03c799087118478655a73f2af6eb71129ac8abd45910cc0108b1`。
- `management-module-api.pdf`：52 个去重文档 Endpoint；SHA-256 `578d8ef4fd436abd7212adaa64863424243820546a3a5f99ead07acb97d12d7f`。

## 导出文件
| 文件 | 类型 | Sheet | 数据行 | 字段 |
|---|---|---|---:|---|
| `download-0005-σ║öτö¿σêùΦí¿.csv` | `.csv` | `<csv>` | 7 | `健康度`, `应用名称`, `Apdex`, `评分`, `responseP50`, `吞吐率 (/s)`, `请求数`, `错误率(%)`, `错误次数`, `慢次数` |
| `download-0006-σ║öτö¿σêùΦí¿.csv` | `.csv` | `<csv>` | 28 | `健康度`, `应用名称`, `Apdex`, `评分`, `responseP50`, `吞吐率 (/s)`, `请求数`, `错误率(%)`, `错误次数`, `慢次数` |
| `download-0007-request_overview-1783315141326.csv` | `.csv` | `<csv>` | 819 | `事务名称`, `应用名称`, `Apdex`, `响应时间中位数(ms)`, `响应时间 P75 (ms)`, `响应时间 P95 (ms)`, `响应时间 P99 (ms)`, `平均请求时间`, `吞吐率 (/s)`, `请求数`, `错误率(%)`, `错误次数`, `慢次数`, `异常次数`, `请求类型` |
| `download-0008-request_overview-1783315145028.csv` | `.csv` | `<csv>` | 862 | `事务名称`, `应用名称`, `Apdex`, `响应时间中位数(ms)`, `响应时间 P75 (ms)`, `响应时间 P95 (ms)`, `响应时间 P99 (ms)`, `平均请求时间`, `吞吐率 (/s)`, `请求数`, `错误率(%)`, `错误次数`, `慢次数`, `异常次数`, `请求类型` |
| `download-0009-request_overview-1783315151325.csv` | `.csv` | `<csv>` | 1000 | `事务名称`, `应用名称`, `Apdex`, `响应时间中位数(ms)`, `响应时间 P75 (ms)`, `响应时间 P95 (ms)`, `响应时间 P99 (ms)`, `平均请求时间`, `吞吐率 (/s)`, `请求数`, `错误率(%)`, `错误次数`, `慢次数`, `异常次数`, `请求类型` |
| `download-0010-request_overview-1783315156829.csv` | `.csv` | `<csv>` | 1000 | `事务名称`, `应用名称`, `Apdex`, `响应时间中位数(ms)`, `响应时间 P75 (ms)`, `响应时间 P95 (ms)`, `响应时间 P99 (ms)`, `平均请求时间`, `吞吐率 (/s)`, `请求数`, `错误率(%)`, `错误次数`, `慢次数`, `异常次数`, `请求类型` |
| `download-0011-Σ║ïσèí.csv` | `.csv` | `<csv>` | 102 | `事务别名`, `名称`, `平均响应时间(ms)`, `总耗时(ms)`, `耗时百分比(%)`, `请求数`, `吞吐率(tps)`, `错误率(%)`, `错误数`, `慢次数`, `应用` |
| `download-0012-Σ║ïσèí.csv` | `.csv` | `<csv>` | 31 | `事务别名`, `名称`, `平均响应时间(ms)`, `总耗时(ms)`, `耗时百分比(%)`, `请求数`, `吞吐率(tps)`, `错误率(%)`, `错误数`, `慢次数`, `应用` |
| `download-0013-µ£ìσèíµÄÑσÅú.csv` | `.csv` | `<csv>` | 398 | `名称`, `应用`, `总耗时(ms)`, `平均响应时间(ms)`, `请求数`, `吞吐率(tps)`, `错误率(%)`, `错误数` |
| `download-0014-ΘöÖΦ»»Φ╢ïσè┐.xlsx` | `.xlsx` | `sheet1` | 97 | `DataTime`, `错误数`, `请求数`, `错误率` |
| `download-0015-ΘöÖΦ»»τ▒╗σ₧ïσêåΦºú.xlsx` | `.xlsx` | `sheet1` | 28 | `DataTime`, `Uncaught Exception`, `HTTP Error Code` |
| `download-0016-ΘöÖΦ»»σêåµ₧É.xls` | `.xls` | `错误分析` | 4 | `序号`, `开始出现时间`, `最后发生时间`, `持续时长`, `错误类型`, `错误名称`, `影响用户数`, `次数`, `发生频率`, `占比`, `应用` |

导出字段只作为用户可见统计语义证据；不得反推 Wire 字段、排序参数或过滤能力。
