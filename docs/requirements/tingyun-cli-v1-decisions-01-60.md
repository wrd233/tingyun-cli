# 听云 APM 新 CLI v1：60 项设计决策记录

> 目的：保留从设计讨论中逐项形成的关键决定、理由、边界和复杂度控制要求。  
> 使用方式：后续实现、Review、Codex Goal 编写与架构变更时，以本文件作为“为什么这样设计”的决策基线。  
> 注意：这里记录的是决策，不替代详细设计文档。

---

## 决策 01：第一消费者是 Agent

**结论**

```text
First-class consumer = Agent
Human role = audit / debug / inspect evidence
```

**理由**

CLI 的首要目标是被 Agent 稳定调用与消费，而不是追求漂亮的人类终端体验。

**优先级**

```text
machine-callable
> stable structure
> clear semantics
> auditable
> pretty terminal output
```

**复杂度控制**

不为了传统 CLI 体验引入多格式输出、交互式菜单或复杂表格渲染。

---

## 决策 02：Evidence Package-first，而不是 Capability-first

**结论**

Agent 默认工作流：

```text
collect
→ Evidence Package
→ Agent 分析
→ 选择对象
→ investigate
```

**理由**

Agent 应聚焦“拿到什么事实”和“下一步查什么”，而不是学习 Endpoint / Capability 组合。

**实现影响**

Capability 保留为内部确定性构件、研究工具和高级调试概念，不是默认 Agent 心智。

---

## 决策 03：Run 是不可变快照

**结论**

```text
collect → new Run
investigate → new Run
任何继续深入 → new Run
```

已有 Run：

- 不覆盖；
- 不回填；
- 不追加后来事实；
- 不原地改 Schema。

**理由**

事实快照必须能回答“当时实际得到了什么”。

---

## 决策 04：名称用于发现，Exact ID 用于执行

**结论**

```text
display name = discovery condition
exact ID / validated target_ref = execution identity
```

**禁止**

CLI 不得模糊匹配名称后静默选择目标。

**实现影响**

先 `discover` 得到真实候选，再由 Agent 选择。

---

## 决策 05：`collect` 使用固定 Core Evidence Package

**结论**

Agent 只提供：

```text
target/source
time_context
```

CLI 固定获取核心证据。

当前核心收束为：

```text
identity
topology
performance
candidates
coverage
```

**禁止**

- quick / standard / deep；
- 模块自由组合；
- include/exclude 参数体系。

---

## 决策 06：时间输入支持相对意图与精确历史时间

**结论**

支持：

```text
last_30m
last_60m
```

以及 exact historical context。

第一条网络请求前：

```text
resolve
→ freeze
→ persist
→ execute
```

**实现影响**

Run 同时保留 requested 与 resolved absolute time。

---

## 决策 07：精确时间不能被静默近似

**结论**

只有已验证 Endpoint Shape 能精确表达时才执行。

例如：

```text
14:10–14:47
```

无法精确表达：

```text
BLOCKED / UNSUPPORTED_TIME_SHAPE
```

**禁止**

自动扩展、缩短、切片、合并或最接近匹配。

---

## 决策 08：Preflight 硬阻断；执行后允许 Partial

**结论**

Preflight 失败：

```text
0 live requests
→ whole run blocked
```

Run 一旦开始：

```text
SUCCESS / EMPTY / FAILED / BLOCKED / SKIPPED
```

分别保留，仍生成不可变 Package。

**总体**

```text
SUCCESS
PARTIAL
```

---

## 决策 09：Raw 与 Normalized Evidence 双层

**结论**

```text
Run/
├── raw/
└── evidence/
```

**职责**

- Raw：审计 Wire Evidence；
- Evidence：Agent 默认消费的归一化事实。

**禁止**

把两者混为一个大 JSON。

---

## 决策 10：Normalized Evidence 按调查领域拆分

**结论**

```text
identity.json
topology.json
performance.json
candidates.json
```

**理由**

Artifact 边界按 Agent 问题组织，而不是 Endpoint 或 Capability。

**禁止**

过度拆分为 nodes/edges/percentiles 等大量小文件。

---

## 决策 11：`manifest.json` 只做 Control Plane + Artifact Index

**结论**

Manifest 回答：

- Run 是什么；
- 来源是谁；
- 时间是什么；
- 有哪些 Artifact；
- 每个 Artifact 状态。

**禁止**

放入：

- slowest action；
- p99 结论；
- 推荐；
- 业务摘要；
- 报告内容。

---

## 决策 12：`coverage.json` 采用两层，但极简

**结论**

```text
Artifact
  ↓
直接产生该 Artifact 的少量 Evidence-producing Steps
```

**不记录**

HTTP 初始化、解析器、serializer、文件写入等内部实现日志。

**目的**

只回答：

```text
这个 Artifact 是什么状态？
为什么？
```

---

## 决策 13：Evidence 只共享极小 Common Envelope

**结论**

统一字段不超过少量概念：

```text
schema_version
kind
status
scope
time_context
derived_from
```

领域 `data` 各自设计。

**禁止**

万能 Entity / Relation / Metric / Observation 模型。

---

## 决策 14：`investigate` 必须从既有 Evidence Item 发起

**结论**

输入：

```text
source_run_id
source_item_ref
```

不允许 Agent 直接传裸：

```text
actionId
actionGuid
traceId
```

**理由**

保持身份来源、选择对象和调查血缘完整。

---

## 决策 15：调查深度由 Agent 通过 Action 分支决定

**结论**

`investigate` 不是固定 Trace Package。

模型：

```text
Agent 选择 Evidence Item
→ 选择 Investigation Action
→ 新 Child Run
→ 再判断
```

**意义**

SQL、Exception、External Call、Call Tree 等可以成为不同调查分支。

---

## 决策 16：默认 Agent Surface 只暴露 Live-Verified Actions

**结论**

```text
Protocol can know more
than
Runtime may expose
```

PARTIALLY_VERIFIED / DOCUMENTED_ONLY 能力：

```text
留在 Research / Protocol
不进入默认 Runtime
```

---

## 决策 17：Evidence Item 可带极简 `available_actions`

**结论**

`available_actions` 只表示：

```text
can
```

不表示：

```text
should
```

**形成条件**

```text
Item kind
+ required identity present
+ action stable
= available
```

**禁止**

推荐、优先级、诊断理由。

---

## 决策 18：`item_ref` 是 Run-local Opaque Reference

**结论**

```text
run-local
opaque
immutable
non-semantic
```

完整身份：

```text
run_id + item_ref
```

**禁止**

- 内容 Hash；
- 全局 Evidence ID；
- 跨 Run 稳定性要求；
- Entity Registry。

---

## 决策 19：顶层心智保留 `discover / collect / investigate`

**结论**

具体 Investigation Action 统一：

```text
investigate(
  source_run_id,
  source_item_ref,
  action
)
```

**不做**

每个 Action 一个一级命令。

**文档要求**

后续设计文档必须详细解释这套三层心智、Action 闭环和取舍。

---

## 决策 20：Live 命令 stdout 只返回极小 Run Receipt

**结论**

```text
stdout
= invocation result
```

完整 Evidence 通过：

```text
manifest
→ artifacts
```

消费。

**禁止**

把大块业务数据复制到 stdout。

---

## 决策 21：Preflight 阻断也创建极简 Blocked Run

**结论**

记录：

- 请求意图；
- 阻断原因；
- `0 live requests`。

**禁止**

创建空的 topology/performance 等伪造 Artifact。

**附加决定**

系统可以维护轻量级日志，但日志不替代 Run。

---

## 决策 22：轻量日志采用 Append-only `runs.jsonl`

**结论**

`runs.jsonl` 只做快速 Run Index。

**记录**

- timestamp；
- command；
- status；
- run_id；
- source；
- action；
- reason_code；
- manifest_path。

**原则**

```text
Run = authoritative
runs.jsonl = disposable index
```

---

## 决策 23：`manifest.overall` 必须确定性派生

**结论**

来源：

```text
Preflight Result
+
Top-level Artifact Coverage
```

不允许 Workflow 自己手工设置一套状态逻辑。

**目的**

避免 Manifest 与 Coverage 状态矛盾。

---

## 决策 24：本地内部 Evidence 保留真实 Wire Identity

**结论**

可保存：

```text
bizSystemId
actionId
actionGuid
traceId
```

前提是它们是后续调查所需业务身份。

**禁止**

Authorization、Cookie、Token、Password、Secret。

**对外**

另走 Sanitized Export。

---

## 决策 25：瞬时只读故障最多自动重试一次

**结论**

适用于明确瞬时故障：

- connect timeout；
- connection reset；
- read timeout；
- selected gateway 5xx。

**要求**

所有 Attempt 可审计。

**禁止**

通用 Retry Framework。

---

## 决策 26：运行期认证失效最多一次 Auth Recovery

**结论**

```text
AUTH_EXPIRED
→ refresh/reacquire once
→ replay same read request once
```

每个 Run 最多一次。

**要求**

与 Transient Retry 分开记录。

---

## 决策 27：一个 Run 内真实请求完全串行

**结论**

```text
max in-flight business requests = 1
```

**原因**

- 稳定；
- 可审计；
- 降低服务端压力；
- 简化 Auth Recovery。

---

## 决策 28：串行请求之间默认最小间隔 2 秒

**结论**

```text
minimum start-to-start interval = 2s
```

**不继承**

历史微实验的 20.1 秒。

**不建设**

动态 Rate Limiter。

---

## 决策 29：Exit Code 只表示 CLI 进程契约

**结论**

只要成功产出可信 Receipt：

```text
SUCCESS / PARTIAL / BLOCKED
→ exit 0
```

非零只表示：

```text
CLI 自身无法完成契约
```

**理由**

避免 Shell Exit Code 成为第二套 Evidence 状态协议。

---

## 决策 30：Provenance 采用极简混合粒度

**结论**

所有 Artifact：

```text
derived_from
```

可调查重要 Item 按需：

```text
source_refs
```

**禁止**

字段级 Provenance、JSONPath、Evidence URI。

---

## 决策 31：旧 Run 永不原地迁移

**结论**

Artifact 有：

```text
schema_version
```

Reader 负责多版本读取。

未来重新解释旧 Raw：

```text
0 live requests
→ new Derived Run
```

但 v1 不建设通用重解释框架。

---

## 决策 32：保留极轻量 `plan-only`

**结论**

只做本地确定性预览。

**严格 0**

- Token；
- HTTP；
- Run；
- `runs.jsonl`；
- Evidence。

**禁止**

Plan ID、Plan File、Resume。

---

## 决策 33：v1 实现极简 Sanitized Export

**结论**

核心资产：

```text
调查过程中沉淀的不可变记录
```

Sanitized Export：

```text
轻量、安全的交付副本
```

**CLI 不负责**

报告生成、结论与建议。

---

## 决策 34：`discover` 真实访问服务端就必须创建 Run

**结论**

Discovery Run：

```text
manifest
coverage
targets.json
raw
```

**不建设**

Target Cache / Target Registry。

---

## 决策 35：`collect` 必须从 Discovery Evidence Item 发起

**结论**

输入：

```text
source_run_id
source_item_ref
time_context
```

不允许直接传裸 `target_ref`。

**复杂度控制**

只做简单 Source Resolution，不引入目标生命周期系统。

---

## 决策 36：`collect` 与 `investigate` 统一 Source Model

**结论**

统一：

```text
source_run_id
source_item_ref
```

CLI 内部只需：

```text
resolve_source(run_id, item_ref)
```

**禁止**

多套 parent / discovery / origin 命名。

---

## 决策 37：配置采用单个本地配置文件

**结论**

```text
default config
+
optional --config override
```

**禁止**

Profile Registry。

Secret 与 Token Cache 位于 Run 之外。

---

## 决策 38：从旧 Evidence 继续时不做隐藏 Live Revalidation

**结论**

只做本地 Contract 校验。

正式 Recipe 的真实结果负责反映：

```text
身份是否仍有效
```

**禁止**

TTL、自动 rediscover、隐藏额外请求。

---

## 决策 39：文件系统是 v1 唯一权威存储

**结论**

每个 Run 是自包含不可变目录。

**不引入**

SQLite 或混合存储。

---

## 决策 40：增加极轻量全局 Live Execution Lock

**结论**

同一时刻只允许一个：

```text
discover / collect / investigate
```

访问服务端。

**定位**

防误操作护栏，不是调度系统。

**冲突**

```text
BLOCKED / LIVE_EXECUTION_BUSY
```

---

## 决策 41：Live Run 使用 `.inflight/` 工作目录

**结论**

```text
执行中 → .inflight/
正常结束 → freeze to runs/
异常中断 → INTERRUPTED Run
```

**禁止**

断点续跑、自动恢复执行。

---

## 决策 42：CLI 启动时轻量检查 stale `.inflight`

**结论**

只处理确认没有活跃进程的目录。

**严格**

```text
0 HTTP
0 Token
0 自动续跑
```

---

## 决策 43：Raw Request 在发送前先落盘

**结论**

顺序：

```text
request_id
→ save request intent
→ send
→ save response/error
→ normalize
```

**目的**

异常中断时尽可能保留已经真实发生的调查过程。

---

## 决策 44：Preflight 冻结当前 Action 的 Execution Envelope

**结论**

不是整场调查的最终计划。

冻结：

- source；
- current action / recipe；
- time context；
- safety；
- auth preparation；
- allowed deterministic continuation。

**运行中**

确定性续接留在当前 Action。

新的调查方向：

```text
available_actions
→ new Child Run
```

---

## 决策 45：不保存 Agent 选择理由

**结论**

调查经验由客观路径自然沉淀：

```text
source item
+ available_actions
+ chosen action
+ child outcome
```

**禁止**

selection_note、Agent reasoning、主观解释进入核心事实层。

---

## 决策 46：Core Collect 不采用固定 Rankings，而采用 Candidate Dataset

**结论**

```text
CLI 获取边界明确的数据集
Agent 自己排序、筛选、组合分析
```

**来源**

Primary Stable Candidate Source 已由真实 Session 证据确定为：

```text
POST /server-api/graph/query/overview?request_overview
```

多组同 scope/time 的 List API 与 Export 对照显示二者候选集合高度一致，而 List API 额外保留 `actionId`、`applicationId` 等真实调查身份，因此更适合作为 v1 Runtime 主来源。

---

## 决策 47：所有 File-native 下载数据最终统一为 CSV

**结论**

Candidate Dataset 的主路径已确定为 JSON-native List API，不强迫经过 CSV。

对于其他只能通过下载获得的 File-native Evidence，无论原始：

```text
CSV
Excel
```

最终形成统一 CSV。

结构：

```text
原始下载文件
→ 统一 CSV
→ candidates.json
```

**原则**

原始文件保留用于审计；统一 CSV 是标准中间层。

---

## 决策 48：Normalized Candidate 只提升已验证语义字段

**结论**

只有已确认：

- 字段语义；
- 单位；
- 聚合方式；

才进入稳定 `candidates.json` Schema。

其他列：

```text
保留在统一 CSV
不猜
```

---

## 决策 49：每条 Candidate 可有 `item_ref`，但不一定可调查

**结论**

```text
item_ref
= 可引用
```

只有：

```text
exact identity complete
+
stable action
```

才出现：

```text
available_actions
```

**禁止**

名称模糊匹配补身份。

---

## 决策 50：`candidates.json` 保留本次获得的全部候选行

**结论**

CLI 不再二次 Top N 裁剪。

**要求**

诚实记录：

```text
FULL
BOUNDED
TOP_N
PAGE_LIMITED
UNKNOWN
```

等数据集边界。

---

## 决策 51：CLI 提供少量 Candidate 本地查看能力

**结论**

不仅让 Agent 自己读完整数据，也提供少量高价值本地操作。

**边界**

这些操作只是既有 Evidence 的本地只读视图：

- 不访问服务端；
- 不创建 Run；
- 不修改 Evidence。

---

## 决策 52：Candidate 本地操作只保留 `all / top / filter`

**结论**

```text
all
top
filter
```

`top` 只支持少数稳定指标。

`filter` 只支持单指标简单比较。

**禁止**

AND / OR、SQL、表达式语言、查询引擎。

---

## 决策 53：Candidate 本地能力放入 `inspect candidates`

**结论**

CLI 结构：

```text
Live:
discover
collect
investigate

Local:
inspect candidates
```

**原因**

避免新增越来越多一级命令。

---

## 决策 54：`inspect candidates` 直接输出 JSON

**结论**

不创建 Run，不生成临时文件，不支持多格式输出。

返回 Item 保留：

```text
source_run_id
item_ref
available_actions
```

便于继续调查。

---

## 决策 55：v1 输入只用少量明确命令行参数

**结论**

不建设：

- JSON Request Envelope；
- stdin RPC；
- Request File；
- 多输入优先级。

**原则**

```text
Input = simple typed flags
Output = stable JSON
```

---

## 决策 56：v1 Runtime CLI 不暴露通用 Endpoint / Capability Executor

**结论**

底层能力只属于：

- Protocol；
- Recipe；
- Test；
- Research Tool。

**未来**

确有需要时再考虑隔离 Developer Surface。

---

## 决策 57：真实 URL 是重要的一等 Evidence

**结论**

业务系统、应用、事务、Trace、数据库 / SQL 等对象，只要 URL 经过验证，就应保留。

**价值**

```text
Evidence
→ Report Agent
→ 用户点击
→ 回到问题现场
```

**禁止**

猜 URL。

---

## 决策 58：URL 缺失不影响核心 Evidence 状态

**结论**

事实完整：

```text
Evidence = SUCCESS
```

即使：

```text
navigation = MISSING
```

**目的**

区分：

```text
事实缺失
vs
现场入口缺失
```

---

## 决策 59：URL 只允许两种可信来源

**结论**

```text
LIVE_OBSERVED
DERIVED_FROM_VERIFIED_ROUTE
```

第二种必须满足：

```text
verified route shape
+ verified parameter mapping
+ exact wire identity
```

不要求每个 URL 都额外访问一次。

---

## 决策 60：Candidate Dataset Source Gate 已由真实 Session 证据解决

**原始决策**

正式实现 Candidate Recipe 前，需要在：

```text
Export / Download
vs
List API
```

中选出一个 `Primary Stable Candidate Source`，且 v1 只实现一条确定性主路径，不做多源 Runtime Fallback。

**解决结果**

真实 Session 已提供足够的多组对照证据，因此不再需要额外验证。最终选择：

```text
POST /server-api/graph/query/overview?request_overview
```

**选择理由**

- 与同 scope/time 的 Export 候选集合在多组样本中高度一致；
- 保留 `actionId`、`applicationId` 等真实 Wire Identity；
- 提供平均响应、P50/P75/P95/P99、吞吐、请求数、错误、慢请求、异常等多维指标；
- 可以直接从 Raw JSON 确定性生成 `candidates.json`；
- 请求更少，转换更少，对服务端更克制。

**已知边界**

- 返回恰好 1000 条时不能默认认为全量；
- 只有真实可证明时才能标记 `FULL`；
- 不通过名称模糊匹配补足调查身份；
- Export / Download 保留为研究验证来源和其他 File-native Evidence 的来源。

**v1**

只实现这一条 Candidate Runtime 主路径，不做运行时多源 fallback。

---

# 结尾：这 60 项决策共同形成的系统

```text
Agent-first
Evidence Package-first
Immutable Run
Read-only
Live-Verified
Low-pressure
Auditable
Branch-aware
URL-aware
Complexity-controlled
```

核心闭环：

```text
discover
→ Discovery Run
→ collect
→ Core Evidence Run
→ Agent 本地分析
→ choose item + action
→ investigate
→ Child Run
→ new evidence
```

最重要的长期原则：

> 不让 CLI 替 Agent 做诊断决策；  
> 不让 Agent 重新承担 Endpoint 与 Wire Contract 复杂度；  
> 不让任何真实调查因为异常中断而凭空消失；  
> 不为了未来可能的扩展，提前建设大而全的框架。
