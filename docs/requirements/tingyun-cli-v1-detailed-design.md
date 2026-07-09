# 听云 APM 新 CLI v1 详细设计文档

> 状态：v1 核心设计已收束；`Candidate Dataset` 主来源已基于真实 Session 证据确定为 List API，不再存在实现前 Live Validation Gate。  
> 适用范围：新一代 `tingyun-cli` v1。  
> 核心定位：**面向 Agent 的、只读的、可审计的 APM 事实获取与调查记录系统。**  
> 非目标：报告生成、自动诊断、通用 API 执行器、任务调度平台、数据仓库。

---

## 1. 文档目的

本设计文档将前期协议研究、Live 验证与 60 个逐项设计决策收束为一套可实施的 v1 架构。

v1 需要解决的核心问题不是“怎样把听云 API 包一层 CLI”，而是：

> 如何让 Agent 在不猜测身份、不猜测参数、不绕过证据边界的前提下，持续获取听云中的真实事实，并把每一次调查过程沉淀成可追溯、可复查、可继续深入的不可变记录。

因此，CLI 的价值不在于输出一份漂亮报告，而在于持续沉淀：

- 当时发现了什么目标；
- 当时请求了什么；
- 服务端真正返回了什么；
- 哪些事实被可靠归一化；
- 哪些信息缺失、失败或被阻断；
- 哪个 Evidence Item 可以继续调查；
- Agent 实际选择了哪一条调查分支；
- 后续 Child Run 又获得了什么；
- 是否存在经过验证的真实页面 URL，可以让用户快速回到问题现场。

后续报告由独立 Agent 基于这些记录完成。

---

## 2. 设计结论总览

### 2.1 第一消费者

```text
First-class consumer = Agent
Human role = audit / debug / inspect evidence
```

冲突时的优先级：

```text
machine-callable
> stable structure
> clear semantics
> auditable
> pretty terminal output
```

### 2.2 顶层心智

```text
discover
  ↓
collect
  ↓
investigate
```

辅助的本地只读能力：

```text
inspect
```

纯本地预览能力：

```text
plan-only
```

安全交付能力：

```text
sanitized export
```

### 2.3 一句话架构

```text
真实服务端
   ↓
Verified Recipe
   ↓
Raw Wire Evidence
   ↓
Normalized Evidence Package
   ↓
Agent 读取与判断
   ↓
选择 Evidence Item + available_action
   ↓
新的不可变 Child Run
```

### 2.4 关键边界

```text
CLI 决定：
- 如何安全、准确地拿事实
- 哪些动作已经 Live-Verified
- 当前 Item 可以合法执行什么
- 如何保留请求、响应、身份与血缘

Agent 决定：
- 哪些事实值得关注
- 候选数据怎样排序、筛选和组合分析
- 下一步选择哪个 available_action
- 何时停止调查
- 如何形成诊断与报告
```

---

# 3. 第一性原则

## 3.1 不猜

绝不猜测：

- ID；
- Trace 身份；
- URL；
- Endpoint 参数；
- 时间范围映射；
- 单位；
- 聚合语义；
- 导出完整性；
- CSV 列含义；
- 路径等价关系。

当证据不足时：

```text
BLOCKED
MISSING
UNKNOWN
BOUNDED
```

都优于“看起来应该可以”。

---

## 3.2 事实记录优先于漂亮输出

CLI 的核心资产是：

```text
Immutable Run
+
Raw Evidence
+
Normalized Evidence
+
Coverage
+
Lineage
```

不是：

```text
诊断报告
总结
建议
漂亮终端表格
```

---

## 3.3 真实访问必须留下记录

原则：

```text
只要真实访问听云服务端
→ 必须形成不可变 Run
```

所以：

- `discover` 产生 Discovery Run；
- `collect` 产生 Core Evidence Run；
- `investigate` 产生 Child Investigation Run；
- Preflight 阻断也产生极简 Blocked Run；
- `plan-only` 因为不访问服务端，所以不产生 Run；
- `inspect` 因为只读本地 Evidence，所以不产生 Run；
- `sanitized export` 是派生交付副本，不产生新 Run。

---

## 3.4 调查路径由证据生长，而不是预先编排

错误模型：

```text
collect
→ trace
→ call tree
→ sql
→ stack
```

正确模型：

```text
Evidence
  ↓
出现新的信息点
  ↓
available_actions
  ↓
Agent 选择
  ↓
Child Run
  ↓
新的 Evidence
```

CLI 不预设整场调查路线。

---

## 3.5 复杂度控制原则

每次出现新需求，先问：

```text
能否放进现有心智？
```

能放：

```text
不新增一级概念
```

必须新增：

```text
只做最小闭环
```

v1 明确避免：

- 通用 Workflow DSL；
- Task Queue；
- Scheduler；
- SQLite Registry；
- Target Registry；
- Global Entity Registry；
- 通用 Endpoint Executor；
- 通用 Retry Framework；
- Rate Limiter Framework；
- Query Engine；
- 脱敏策略 DSL；
- URL 路由系统；
- 通用 CSV Schema Registry。

---

# 4. 与 Capability Protocol 的关系

## 4.1 协议层与运行层分离

```text
Protocol / Research Layer
可以知道更多

Runtime Stable Surface
只暴露 Live-Verified 能力
```

协议中可以存在：

```text
VERIFIED
PARTIALLY_VERIFIED
DOCUMENTED_ONLY
```

但默认 Agent Action Surface 只允许：

```text
Live-Verified
```

### 4.2 底层结构

```text
Endpoint / Variant
  ↓
Atomic Capability
  ↓
few deterministic Recipe
  ↓
discover / collect / investigate
```

### 4.3 v1 不暴露通用底层执行器

正式 Runtime CLI 不提供：

```text
endpoint execute
capability run
generic request
```

这些只属于：

- Protocol；
- Recipe 内部构件；
- 研究工具；
- 微实验。

未来确有需要时，可以另建严格隔离的 Developer Surface，但不进入 v1。

---

# 5. CLI 顶层命令设计

## 5.1 `discover`

目的：

> 从听云真实服务端发现目标候选，并形成不可变 Discovery Run。

输入：

- 目标类型；
- 必要的少量过滤参数（仅在已验证时）；
- 配置文件可选覆盖。

输出：

```text
stdout = Run Receipt
```

Run 中保存：

```text
manifest.json
preflight.json
coverage.json
evidence/targets.json
raw/*
```

Discovery Candidate：

```json
{
  "item_ref": "item-0003",
  "kind": "business_system_candidate",
  "display_name": "业务系统 A",
  "target_ref": "...",
  "wire_identity": {
    "biz_system_id": "..."
  }
}
```

注意：

- display name 只是发现条件与人类可读信息；
- exact Wire Identity 才是执行身份；
- CLI 不模糊匹配名字后静默选中目标。

---

## 5.2 `collect`

目的：

> 对一个已经通过 Discovery Evidence 选中的真实目标，生成固定 Core Evidence Package。

输入统一为：

```text
source_run_id
source_item_ref
time_context
```

不允许直接传裸：

```text
target_ref
bizSystemId
```

解析流程：

```text
source_run_id + source_item_ref
  ↓
找到 business_system_candidate
  ↓
读取已保存的 exact target_ref / Wire Identity
  ↓
校验 time_context
  ↓
Preflight
  ↓
执行固定 Core Collect
```

v1 Core Collect：

```text
identity
topology
performance
candidates
coverage
```

不提供：

```text
quick / standard / deep
模块自由组合
include_xxx
exclude_xxx
```

同类 Run 必须结构可比较。

---

## 5.3 `investigate`

目的：

> 从已有 Evidence Item 沿一个已验证 Investigation Action 继续深入。

输入：

```text
source_run_id
source_item_ref
action
```

流程：

```text
resolve_source(run_id, item_ref)
  ↓
确认 Item 存在
  ↓
确认 action 出现在 available_actions
  ↓
确认 action 仍在 Stable Surface
  ↓
Preflight
  ↓
执行该 Action
  ↓
生成不可变 Child Run
```

关键边界：

```text
Agent 决定查哪个 Item、选哪个 action
CLI 决定该 action 怎样可靠获取事实
```

v1 不允许直接传裸：

```text
actionId
actionGuid
traceId
```

这样可以避免：

- ID 抄错；
- 来源不明；
- 调查理由与 Evidence 脱节；
- Lineage 断裂。

---

## 5.4 `inspect`

定位：

```text
本地只读查看
```

v1 首先只实现：

```text
inspect candidates
```

操作：

```text
all
top
filter
```

它们：

- 不访问服务端；
- 不创建 Run；
- 不写 `runs.jsonl`；
- 不修改 Evidence；
- 不生成新的事实；
- 只产生临时本地视图。

输出：

```text
stdout = actual JSON result
```

与 Live 命令不同。

---

## 5.5 `plan-only`

定位：

```text
Local Deterministic Preview
```

只做：

- 解析输入；
- 验证本地 source；
- 检查时间形状是否可以精确表达；
- 检查 Stable Capability / Action；
- 列出预计步骤；
- 估算预计请求数量。

严格不做：

- Token 请求；
- HTTP；
- Run；
- `runs.jsonl`；
- Evidence；
- Plan ID；
- Plan 文件；
- Resume；
- 缓存执行结果。

---

# 6. 统一来源引用模型

所有“从已有 Evidence 继续前进”的输入统一为：

```text
source_run_id
+
source_item_ref
```

所以：

```text
discover
→ 无 source

collect
→ source + time_context

investigate
→ source + action
```

内部只需要一个核心解析器：

```text
resolve_source(run_id, item_ref)
```

不建设：

- `discovery_run_id`；
- `parent_run_id`；
- `selection_origin`；
- `investigation_origin`；
- 通用 Lineage Object。

Lineage 使用少量确定字段即可。

---

# 7. Run 模型

## 7.1 Run 是不可变快照

```text
collect → new Run
investigate → new Run
任何继续深入 → new Run
```

已有 Run：

- 永不覆盖；
- 永不回填业务证据；
- 永不追加后来获得的事实；
- 永不原地升级 Schema；
- 永不原地重新解释。

---

## 7.2 Run 类型

v1 最少需要：

```text
DISCOVERY
COLLECT
INVESTIGATION
BLOCKED
INTERRUPTED
```

注意：

- `BLOCKED` 是一次确定性拒绝记录；
- `INTERRUPTED` 是一次真实执行中断记录；
- 不需要引入复杂状态机。

---

## 7.3 目录布局

```text
data-root/
├── runs/
│   └── run-xxx/
│       ├── manifest.json
│       ├── preflight.json
│       ├── coverage.json
│       ├── evidence/
│       └── raw/
├── .inflight/
├── runs.jsonl
└── exports/
```

其他可变状态位于 Run 体系外：

```text
config
token cache
credentials
```

---

## 7.4 文件系统是唯一权威存储

```text
Filesystem
= authoritative
```

不引入：

- SQLite；
- DB Registry；
- File + DB 双写；
- Storage Backend Interface；
- S3 Backend；
- Remote Artifact Store。

---

# 8. `.inflight` 与异常中断

## 8.1 执行期目录

Live Run 执行期间先写：

```text
.inflight/run-xxx/
```

正常完成：

```text
生成最终 Manifest / Coverage
→ 冻结
→ 原子移动到 runs/run-xxx/
```

---

## 8.2 异常退出

如果进程被 kill、机器重启或异常崩溃：

```text
保留已有 Raw Evidence
→ 不自动删除
→ 后续冻结成 INTERRUPTED Run
```

明确不做：

- 断点续跑；
- 自动继续请求；
- 后台恢复服务；
- 复杂 Task State Machine。

---

## 8.3 CLI 启动时轻量检查

每次 CLI 启动：

```text
quick stale .inflight check
```

只检查：

- 是否仍有活跃进程；
- 确认 stale 后才冻结。

严格：

```text
0 HTTP
0 Token
0 自动续跑
```

不扫描所有历史 Run。

---

# 9. Evidence Package 结构

## 9.1 典型 Collect Run

```text
run-xxx/
├── manifest.json
├── preflight.json
├── coverage.json
├── evidence/
│   ├── identity.json
│   ├── topology.json
│   ├── performance.json
│   └── candidates.json
└── raw/
    ├── request-0001.json
    ├── response-0001.json
    ├── request-0002.json
    ├── response-0002.json
    └── ...
```

如果存在下载：

```text
raw/
├── request-0004.json
├── response-0004.json
├── download-0004.xlsx
└── download-0004.csv
```

如果原始就是 CSV，则不重复保存第二份同内容 CSV。

---

# 10. `manifest.json`

## 10.1 定位

```text
Package Control Plane
+
Artifact Index
```

不是：

- 业务摘要；
- 诊断结论；
- 报告；
- 推荐。

回答：

```text
Run 是什么？
目标是谁？
时间范围是什么？
来源是谁？
有哪些 Artifact？
每个 Artifact 什么状态？
入口在哪里？
```

示例：

```json
{
  "schema_version": 1,
  "run_id": "run-...",
  "run_type": "COLLECT",
  "overall": "PARTIAL",
  "source": {
    "run_id": "run-discovery-...",
    "item_ref": "item-0003"
  },
  "time_context": {
    "requested": {
      "kind": "relative",
      "value": "30m"
    },
    "resolved": {
      "start_time": "...",
      "end_time": "..."
    }
  },
  "artifacts": [
    {
      "kind": "identity",
      "path": "evidence/identity.json",
      "status": "SUCCESS"
    }
  ],
  "coverage_ref": "coverage.json"
}
```

---

## 10.2 `overall` 计算

`manifest.overall` 不是手工独立设置。

来源：

```text
Preflight Result
+
Top-level Artifact Coverage
```

规则：

```text
Preflight BLOCKED
→ overall = BLOCKED
```

真实执行后：

```text
所有应产生的核心 Artifact
均为 SUCCESS / EMPTY
→ overall = SUCCESS
```

存在核心 Artifact：

```text
FAILED / BLOCKED / missing
→ overall = PARTIAL
```

`EMPTY` 是可信查询结果，不等于失败。

---

# 11. `preflight.json`

## 11.1 定位

`preflight.json` 不是：

```text
整场调查的最终路线
```

而是：

```text
当前这一次 collect / investigation action 的冻结执行边界
```

---

## 11.2 冻结内容

第一条真实请求前，冻结：

- 当前 source；
- 当前 run type；
- 当前 action / collect recipe；
- requested time context；
- resolved absolute time context；
- Stable Recipe / Protocol reference；
- 安全检查结果；
- Auth preparation 状态（无凭据）；
- Live Execution Lock 结果；
- 已知初始步骤；
- 允许的确定性续接边界。

不需要预知：

```text
Agent 下一步会查 SQL 还是 Call Tree
```

---

## 11.3 运行期分叉

### 确定性续接

例如：

```text
Request A
→ 返回 actionGuid + traceId
→ Request B
```

如果 B 是完成当前 Action 所必需，且血缘已经 Live-Verified：

```text
可以留在当前 Action 内继续
```

### 新调查方向

例如：

```text
Trace 发现数据库异常
```

可能产生：

```text
inspect_database
inspect_call_tree
inspect_external_call
```

此时：

```text
生成 Evidence Item.available_actions
→ 当前 Run 结束
→ Agent 选择
→ 新 Child Run
```

---

# 12. `coverage.json`

## 12.1 只回答两个问题

```text
这个 Artifact 最终是什么状态？
为什么是这个状态？
```

不是：

- Workflow Trace；
- HTTP Client Log；
- 第二份 Manifest。

---

## 12.2 两层结构

```text
Artifact
  ↓
直接产生该 Artifact 的少量 Evidence-producing Steps
```

不继续展开：

```text
HTTP init
parse
serializer
file write
```

示例：

```json
{
  "overall": "PARTIAL",
  "artifacts": {
    "topology": {
      "status": "SUCCESS",
      "steps": [
        {
          "capability": "read_business_topology",
          "status": "SUCCESS",
          "evidence_refs": [
            "raw/response-0002.json"
          ]
        }
      ]
    },
    "performance": {
      "status": "EMPTY",
      "steps": [
        {
          "capability": "read_business_performance",
          "status": "EMPTY"
        }
      ]
    }
  }
}
```

状态：

```text
SUCCESS
EMPTY
FAILED
BLOCKED
SKIPPED
```

语义必须明确：

```text
EMPTY
= 请求成功且可信，但没有数据

FAILED
= 已尝试，未获得可信事实

BLOCKED
= 因前置条件或安全条件未执行

SKIPPED
= Recipe 确定性判断本次不需要
```

---

# 13. Normalized Evidence Common Envelope

四个核心 Artifact：

```text
identity.json
topology.json
performance.json
candidates.json
```

只共享极小公共外壳。

建议概念：

```text
schema_version
kind
status
scope
time_context
derived_from
```

领域 `data` 各自独立。

禁止设计：

```text
万能 Entity / Relation / Metric / Observation 模型
```

也不引入复杂 JSON Pointer 引用协议。

轻微重复优于复杂内部引用。

---

# 14. Raw Evidence

## 14.1 地位

```text
Raw
= 当时真实请求与响应的可审计 Wire Evidence
```

Normalized Evidence 必须可回溯到 Raw。

---

## 14.2 请求落盘顺序

每次真实请求：

```text
1. 生成 request_id
2. 原子保存非敏感 Request Record
3. 发出真实请求
4. 原子保存 Response / Error Record
5. 再做 Normalization
```

原子写可采用：

```text
tmp file
→ rename
```

不需要数据库事务。

---

## 14.3 Request Record

只保存：

- request_id；
- endpoint_id；
- variant_id；
- method；
- path；
- query / body；
- 非秘密 metadata；
- attempt 信息。

不保存：

- Authorization；
- Cookie；
- Token；
- Password；
- Secret；
- 无意义的全部 Header；
- TLS 噪音。

---

# 15. Provenance

## 15.1 Artifact 级默认

所有 Evidence Artifact：

```text
derived_from
```

指向 Run 内相对 Raw 路径。

---

## 15.2 Item 级按需

只有：

```text
带 item_ref
且可驱动后续调查的重要 Item
```

按需增加：

```text
source_refs
```

不做：

- 字段级 Provenance；
- 每个时间序列点来源；
- JSONPath；
- Evidence URI；
- Provenance Registry。

---

# 16. `item_ref`

性质：

```text
run-local
opaque
immutable
non-semantic
```

例如：

```text
item-0001
```

完整身份：

```text
run_id + item_ref
```

不追求：

- 跨 Run 稳定；
- 内容 Hash；
- 全局唯一实体 ID；
- Global Evidence Registry。

同一业务对象在不同 Run 中拥有不同 `item_ref` 完全正常。

---

# 17. `available_actions`

## 17.1 定位

```text
can
≠
should
```

它只表示：

> 当前 Item 是否具备一条已经 Live-Verified、身份完整、可合法执行的下一步路径。

不表示：

> CLI 推荐你调查它。

---

## 17.2 形成规则

```text
Evidence Item Kind
+
Required Verified Identity Present
+
Action Is Stable
=
Available
```

例如：

```text
action_ranking
+
actionId present
+
investigate_trace stable
=
available
```

---

## 17.3 不做推荐

不保存：

- priority；
- recommended_action；
- recommendation_reason；
- Agent reasoning；
- selection_note。

---

# 18. Investigation Action 模型

## 18.1 不是固定 Trace Package

错误：

```text
investigate
→ 固定 Trace Detail + Call Tree
```

正确：

```text
Agent-driven Stable Investigation Actions
```

每次 Action：

```text
读取已有 Evidence Item
→ 执行一条已验证调查动作
→ 产生新的不可变 Child Run
```

---

## 18.2 Stable Surface

默认只暴露 Live-Verified Actions。

例如当前成熟主链：

```text
ranking / candidate item
→ investigate_trace

trace identity
→ inspect_call_tree
```

数据库、SQL、Stack、NoSQL、MQ 等即使协议资料丰富，但未达到同等 Live-Verified 深度前：

```text
留在 Protocol / Research
不进入默认 Agent Surface
```

---

## 18.3 调查经验如何沉淀

不保存主观理由。

客观路径已经足够：

```text
Source Evidence Item
  ↓
available_actions
  ↓
Agent chosen action
  ↓
Child Run outcome
```

未来可以从大量真实路径总结：

- 哪类 Evidence 通常走向哪类分支；
- 哪些 Action 经常产生有效证据；
- 哪些分支经常 EMPTY；
- 某类问题怎样逐步缩小范围。

v1 不建设“经验数据库”。

---

# 19. Time Context

## 19.1 输入

支持：

```text
relative intent
例如 last_30m / last_60m
```

和：

```text
exact historical context
```

---

## 19.2 执行前解析

第一条网络请求前：

```text
resolve
→ freeze
→ persist
→ first network request
```

Run 中同时保留：

```text
requested time
+
resolved absolute time
```

同一 Run 内所有 Capability 共享同一个冻结时间上下文。

---

## 19.3 不允许近似

如果请求：

```text
14:10–14:47
```

而已验证 Shape 只能精确表达 30/60 分钟：

```text
BLOCKED
reason = UNSUPPORTED_TIME_SHAPE
```

绝不：

- 自动扩展；
- 自动缩短；
- 拆分；
- 合并；
- 偷偷改成最接近窗口。

---

# 20. Core Collect

## 20.1 固定结构

```text
identity
topology
performance
candidates
coverage
```

不做自由模块组合。

---

## 20.2 Identity

回答：

```text
这个目标到底是谁？
```

应保存：

- display name；
- target_ref；
- exact Wire Identity；
- 可验证的目标类型；
- 已验证 URL（如有）。

---

## 20.3 Topology

回答：

```text
这个业务系统由什么构成？
运行时间窗口内发生了哪些调用关系？
```

必须区分：

```text
Structural Topology
vs
Time-window Runtime Edge
```

不能把两者混为一谈。

---

## 20.4 Performance

回答：

```text
这个目标在冻结时间窗口内表现如何？
```

指标必须保留：

```text
scope
semantic
aggregation
unit
time_context
shape
```

例如响应平均值与百分位必须明确区分。

---

## 20.5 Candidates

回答：

```text
有哪些可供 Agent 本地分析与后续选择的调查候选？
```

不是：

```text
CLI 已经替 Agent 排好的榜单
```

---

# 21. Candidate Dataset 设计

## 21.1 核心原则

```text
CLI
→ 获取边界明确、尽量完整的数据集

Agent
→ 自己按响应、P99、错误率、吞吐等维度分析
```

避免为了不同排序反复请求服务端。

---

## 21.2 Primary Stable Source：List API

`Candidate Dataset` 的 v1 稳定主来源已经确定为：

```text
POST /server-api/graph/query/overview?request_overview
```

该决定由真实 Session 中多组“页面 List API ↔ 同 scope/time 导出文件”对照证据支持。当前证据表明：

- List API 与对应导出在多组样本中获得相同的候选行集合与行数；
- List API 保留 `actionId`、`applicationId` 等继续调查所需的真实 Wire Identity；
- 对应导出文件主要保留展示字段和指标，但会丢失关键执行身份；
- List API 直接返回 JSON，可直接进入 Raw JSON → Normalized Evidence，不需要为了 Candidate Dataset 额外走下载、Excel/CSV 转换链；
- List API 一次即可提供平均响应、P50/P75/P95/P99、吞吐、请求数、错误、慢请求、异常等多维指标，更适合 Agent 本地排序和筛选；
- 使用 List API 可以减少请求数量和服务端压力。

因此 v1：

```text
Primary Candidate Source
= request_overview List API
```

明确不做：

```text
Export 失败 → List API → Ranking fallback
List API 失败 → 自动切换 Export
运行时多源 fallback
```

### 数据集完整性边界

`request_overview` 当前没有足够证据证明所有 scope 下都返回全量。真实 Session 中存在返回恰好 1000 条的情况，因此：

- 不得默认标记为 `FULL`；
- 必须记录 `row_count`；
- 只有存在可证明的完整性依据时才使用 `FULL`；
- 命中已观察到的边界或无法证明全量时，应使用克制的 `BOUNDED` / `UNKNOWN` 语义；
- 不得把“当前拿到 1000 条”解释为“系统总共只有 1000 条”。

具体完整性枚举保持最少，只表达真实可证明的边界。

---

## 21.3 下载文件处理

Candidate Dataset 的主路径是 JSON-native：

```text
List API JSON
→ Raw JSON
→ candidates.json
```

不为了统一形式而强迫 Candidate Dataset 经过 CSV。

对于其他只能通过文件获得的 File-native Evidence Source，无论原始格式是：

```text
CSV
Excel
```

最终都形成统一 CSV。

三层：

```text
原始下载文件
= 审计

统一 CSV
= 确定性标准中间层

Normalized Evidence
= Agent 默认消费层
```

例如：

```text
raw/
├── download-0004.xlsx
└── download-0004.csv

evidence/
└── candidates.json
```

原始就是 CSV 时，不重复存两份同内容文件。

---

## 21.4 字段提升规则

`candidates.json` 只提升：

```text
字段语义
单位
聚合方式
```

已经验证清楚的核心字段。

未验证列：

```text
留在统一 CSV
不猜
不进入稳定 Schema
```

---

## 21.5 数据集边界

必须记录：

```text
scope
row_count
completeness
source_format
```

可能状态：

```text
FULL
BOUNDED
TOP_N
PAGE_LIMITED
UNKNOWN
```

只使用能被真实证明的状态。

---

## 21.6 不二次裁剪

```text
服务端真实给多少
且属于本次已知边界
→ candidates.json 保留多少
```

CLI 不再裁成 Top N。

不建设分页或本地数据库。

---

## 21.7 Candidate Item

每条记录可以有：

```text
item_ref
```

方便：

- Agent 排序；
- Agent 引用；
- Agent 选择。

但只有满足：

```text
exact Wire Identity complete
+
Stable Action available
```

才附带：

```text
available_actions
```

绝不通过名称模糊匹配补足调查链。

---

# 22. Candidate 本地查看

## 22.1 仅三种

```text
all
top
filter
```

### `all`

返回全部 Candidate Dataset。

### `top`

只允许少量已验证核心指标，例如：

```text
response_avg
p99
error_rate
throughput
```

具体列表以 Candidate Schema 为准。

### `filter`

只支持：

```text
metric
operator
value
```

例如：

```text
p99 > 5000
error_rate > 5
```

不支持：

- AND / OR；
- 括号；
- SQL；
- 函数；
- 任意表达式；
- 自定义未验证列。

复杂分析交给 Agent。

---

## 22.2 输出

`inspect candidates` 直接输出 JSON。

返回 Item 必须保留原始：

```text
source_run_id
item_ref
available_actions
```

以便继续调查。

---

# 23. Verified URL / Navigation Evidence

## 23.1 URL 是一等重要证据

因为真实工作流是：

```text
Evidence
→ Agent 分析
→ 报告指出问题
→ 用户点击 URL
→ 回到听云问题现场
```

CLI 不生成报告，但应保留已验证导航入口。

---

## 23.2 URL 来源只允许两种

### `LIVE_OBSERVED`

Exact URL 本身真实访问过。

### `DERIVED_FROM_VERIFIED_ROUTE`

必须同时满足：

```text
已验证 Route Shape
+
已验证 URL 参数 ↔ Wire Identity 映射
+
当前 exact Wire Identity
=
确定性 URL
```

不是猜测。

---

## 23.3 URL 缺失不影响核心 Evidence 状态

例如：

```text
trace evidence = SUCCESS

navigation = MISSING
reason = URL_NOT_VERIFIED
```

核心 Evidence：

```text
SUCCESS / PARTIAL
```

与：

```text
navigation coverage
```

分开。

---

# 24. Execution Safety

## 24.1 单 Run 完全串行

```text
max in-flight business requests = 1
```

目的：

- 确定性；
- 可审计；
- 低服务端压力；
- 简化 Auth Recovery；
- 简化失败处理。

---

## 24.2 固定最小请求间隔

v1 默认：

```text
minimum start-to-start interval = 2s
```

不继承历史微实验的 20.1 秒。

不建设：

- adaptive rate limiter；
- jitter；
- per-endpoint pacing；
- 动态策略。

---

## 24.3 全局 Live Execution Lock

同一时刻只允许一个：

```text
discover / collect / investigate
```

真实访问服务端。

它只是防误操作护栏。

冲突：

```text
BLOCKED
reason = LIVE_EXECUTION_BUSY
0 live requests
```

不做：

- 排队；
- 等待调度；
- Worker；
- Priority。

---

# 25. Retry 与 Auth Recovery

## 25.1 Transient Retry

只对极少数明确瞬时故障：

- connect timeout；
- connection reset；
- read timeout；
- selected gateway 5xx。

最多：

```text
1 次自动重试
```

所有 Attempt 可审计。

不重试：

- 4xx；
- 业务错误；
- EMPTY；
- 安全阻断；
- 参数错误；
- 身份不合法；
- 确定性解析错误。

---

## 25.2 Auth Recovery

运行中明确认证失效：

```text
每个 Run 最多 1 次 Auth Recovery
```

流程：

```text
attempt 1
→ AUTH_EXPIRED
→ refresh / reacquire once
→ replay same read request once
```

严格：

- 不改变请求参数；
- 不改变冻结时间；
- 不写入任何 Token；
- 不循环刷新。

Transient Retry 与 Auth Recovery 分开记录。

---

# 26. Config 与 Secret

## 26.1 配置模型

```text
一个明确的本地配置文件
+
可选 --config 覆盖
```

不建设 Profile Registry。

多环境：

```text
使用不同 config 文件
```

---

## 26.2 Secret 边界

凭据不能通过普通命令参数传入。

永远不能进入：

- Run；
- Raw；
- Evidence；
- `runs.jsonl`；
- Sanitized Export。

Token Cache 位于 Runs 之外。

---

# 27. Preflight 阻断

即使 Preflight 阻断，也创建极简不可变 Blocked Run。

例如：

```text
manifest.json
preflight.json
coverage.json
```

没有：

```text
evidence/*
raw live response
```

并明确：

```text
live_request_count = 0
```

绝不创建空的 `topology.json` 等伪造 Artifact。

---

# 28. 状态与退出码

## 28.1 Run 状态

```text
SUCCESS
PARTIAL
BLOCKED
INTERRUPTED
```

Artifact / Step 可有：

```text
SUCCESS
EMPTY
FAILED
BLOCKED
SKIPPED
```

---

## 28.2 Exit Code

原则：

```text
Process Outcome
≠
Evidence Outcome
```

只要 CLI 成功完成确定性处理并产出可信 Receipt：

```text
SUCCESS
PARTIAL
BLOCKED
→ exit 0
```

非零只表示：

- CLI 崩溃；
- 内部 Bug；
- Run 无法持久化；
- Manifest / Receipt 无法可靠形成；
- 调用者不能依赖正常 Evidence Contract。

不建设复杂 Exit Code 表。

---

# 29. stdout Contract

## 29.1 Live 命令

```text
discover
collect
investigate
```

stdout 只输出极小稳定 Run Receipt：

```json
{
  "schema_version": 1,
  "command": "collect",
  "status": "PARTIAL",
  "run_id": "run-...",
  "manifest_path": ".../manifest.json"
}
```

不输出完整 Evidence。

---

## 29.2 Local inspect

```text
inspect
```

stdout 输出实际 JSON 结果。

---

# 30. Lightweight Run Index

文件：

```text
runs.jsonl
```

append-only。

用途：

- 最近运行了什么；
- Run 在哪里；
- 结果是什么；
- 父子关系；
- Action；
- 阻断原因。

只记录少量元数据。

不保存：

- 业务事实；
- actionId；
- traceId；
- Topology；
- Metrics；
- Stack；
- 完整错误响应。

原则：

```text
Run = authoritative

runs.jsonl = disposable index
```

必须可以从 Run 重建。

---

# 31. Schema Evolution

旧 Run：

```text
永不原地迁移
永不重写
```

Artifact 使用：

```text
schema_version
```

Reader 按版本读取。

未来确实需要新逻辑重新解释旧 Raw：

```text
Original Run
  ↓
0 live requests
  ↓
New Derived Run
```

但 v1 不实现通用 Reinterpretation Framework。

---

# 32. Sanitized Export

## 32.1 定位

```text
Internal Run
= 可执行、可继续调查

Sanitized Export
= 轻量、安全、只读交付副本
```

核心资产仍是 Run。

报告由独立 Agent 完成。

---

## 32.2 v1 只做固定规则

例如：

- 移除真实业务 ID；
- 移除内部地址；
- 移除本地绝对路径；
- 再次确认无 Token / Cookie / Authorization；
- 保留结构、类型、语义与证据血缘。

不建设：

- Policy DSL；
- 多 Profile；
- 可逆映射仓库；
- 自定义 Mask Framework。

Sanitized Export：

- 不创建 Run；
- 不写 `runs.jsonl`；
- 不允许继续 `investigate`；
- 不应保留可误导的可执行 `available_actions`。

---

# 33. 输入协议

v1 只使用：

```text
少量明确、强类型命令行参数
```

不建设：

- JSON Request Envelope；
- stdin RPC；
- Request File；
- flags / stdin / file 多入口。

机器可读性集中在稳定 JSON 输出。

---

# 34. 旧 Evidence 的执行语义

从旧 Evidence Item 继续：

```text
只做本地 Contract 校验
```

检查：

- Run 存在；
- Item 存在；
- Item kind 合法；
- 所需 Wire Identity 完整；
- Action 仍在 Stable Surface；
- Action 出现在 Item 的 `available_actions`。

不额外访问服务端重新验证对象。

正式 Recipe 的真实结果负责反映：

```text
对象是否仍有效
```

不建设：

- TTL；
- 自动 rediscover；
- hidden live revalidation；
- freshness registry。

---

# 35. 设计中的核心调查路径

```text
discover
  ↓
Discovery Run
  ↓ Agent 选择 target item
collect
  ↓
Core Evidence Run
  ↓ Agent 分析 candidates / topology / performance
选择 source item + available_action
  ↓
investigate
  ↓
Child Run
  ↓
新的 Evidence
  ↓
新的 available_actions
```

这条链本身就是：

```text
真实调查路径记录
```

---

# 36. v1 明确不做的事情

- 写诊断报告；
- 自动根因分析；
- 主观推荐下一步；
- Agent reasoning 保存；
- 通用 Endpoint Executor；
- 通用 Capability Runner；
- 自由 Workflow 编排；
- 自动多分支展开；
- SQL / Stack / MQ 等未晋级能力的默认暴露；
- SQLite；
- 任务队列；
- 并发调度；
- 高级限流；
- 多 Profile Registry；
- Target Registry；
- Global Entity Registry；
- Candidate Query Engine；
- 通用 CSV/Excel 平台；
- 通用脱敏平台；
- URL Router；
- 断点续跑；
- 自动恢复执行；
- 多格式终端输出；
- 通用 Schema Migration Framework。

---

# 37. Candidate Dataset Source 决策已解决

## 37.1 最终结论

```text
Primary Stable Candidate Source
= POST /server-api/graph/query/overview?request_overview
```

不再需要新的 Candidate Source Micro-Experiment，且该事项不再构成实现门槛。

## 37.2 证据基础

真实 Session 已完成多组 List API 与同 scope/time Export 的对照。其关键结论是：

1. 多组样本中 List API 与导出文件候选集合、行数和顺序高度一致；
2. List API 保留 `actionId`、`applicationId` 等真实 Wire Identity；
3. 导出文件会丢失关键 ID，因此更适合审计和研究对照，而不是 v1 Candidate Runtime 主来源；
4. List API 提供多维指标，可支持 Agent 在本地自行按平均响应、P99、错误率、吞吐等维度分析；
5. List API 请求链更短、转换更少、服务端压力更低。

## 37.3 已知边界

- 不能把返回 1000 条直接解释为全量；
- `row_count == 1000` 或其他无法证明全量的场景必须保持克制的完整性语义；
- Candidate Item 只有在具备真实 Wire Identity 且对应 Action 已进入 Stable Surface 时，才出现 `available_actions`；
- 不通过名称模糊匹配补足身份。

## 37.4 Export 的新角色

Export / Download 不再是 Candidate Dataset 的 Primary Runtime Source。它保留为：

```text
Research Validation Source
+
File-native Evidence Source
```

未来只有当某类证据无法通过稳定 JSON API 获取时，才使用：

```text
Original Download
→ Unified CSV
→ Normalized Evidence
```

不建设运行时多源 fallback。

---

# 38. 建议的 v1 模块边界

以下只是实现组织建议，不要求设计成插件框架。

```text
src/tingyun_cli/
├── cli.py
├── config.py
├── auth.py
├── protocol/
├── recipes/
│   ├── discover.py
│   ├── collect.py
│   └── investigate.py
├── runtime/
│   ├── preflight.py
│   ├── executor.py
│   ├── pacing.py
│   ├── live_lock.py
│   └── inflight.py
├── evidence/
│   ├── manifest.py
│   ├── coverage.py
│   ├── raw.py
│   ├── normalize.py
│   └── refs.py
├── inspect/
│   └── candidates.py
├── export/
│   └── sanitize.py
└── storage/
    └── filesystem.py
```

原则：

- 目录是为了保持边界；
- 不引入抽象基类体系；
- 不提前设计 Provider Registry；
- 不为了“扩展性”建设插件机制。

---

# 39. 核心 Schema 建议

## 39.1 Run Receipt

```json
{
  "schema_version": 1,
  "command": "collect",
  "status": "SUCCESS",
  "run_id": "run-...",
  "manifest_path": ".../manifest.json"
}
```

Blocked：

```json
{
  "schema_version": 1,
  "command": "collect",
  "status": "BLOCKED",
  "run_id": "run-...",
  "manifest_path": ".../manifest.json",
  "reason_code": "UNSUPPORTED_TIME_SHAPE"
}
```

---

## 39.2 Candidate Item

```json
{
  "item_ref": "item-0042",
  "kind": "candidate",
  "name": "...",
  "metrics": {
    "p99": {
      "value": 5000,
      "unit": "ms"
    },
    "error_rate": {
      "value": 5,
      "unit": "percent"
    }
  },
  "wire_identity": {
    "action_id": 123456
  },
  "available_actions": [
    "investigate_trace"
  ],
  "source_refs": [
    "raw/download-0004.csv"
  ]
}
```

没有可执行身份时，可省略：

```text
wire_identity
available_actions
```

---

## 39.3 Verified Link

```json
{
  "url": "...",
  "verification": "LIVE_OBSERVED"
}
```

或：

```json
{
  "url": "...",
  "verification": "DERIVED_FROM_VERIFIED_ROUTE"
}
```

---

# 40. Acceptance Criteria

v1 至少应满足以下条件。

## 40.1 Agent Contract

- Agent 可以只通过 `discover → collect → investigate` 完成主路径；
- 不需要理解 Endpoint / Variant；
- 不需要传裸业务 ID；
- Live 命令 stdout 始终是稳定 JSON Receipt；
- `inspect` 返回稳定 JSON。

## 40.2 Evidence

- 所有真实服务端访问都有 Run；
- Raw Request 在发送前落盘；
- Response / Error 返回后立即落盘；
- Normalized Evidence 可回溯到 Raw；
- Run 完成后不可修改；
- 旧 Run 不原地迁移。

## 40.3 Safety

- 只读；
- 单 Run 串行；
- 全局最多一个 Live Run；
- 2 秒最小 start-to-start；
- 最多一次瞬时重试；
- 最多一次 Auth Recovery；
- Secret 不进入 Run。

## 40.4 Failure

- Preflight 阻断形成 Blocked Run；
- 0 live requests 可审计；
- Partial Run 仍然产出 Package；
- Interrupted Run 保留已有记录；
- `exit 0` 与 Evidence 状态分离。

## 40.5 Candidate Dataset

- Primary Source 已通过专项 Live Validation；
- Raw 下载原样保留；
- Excel 最终转统一 CSV；
- Normalized 只提升已验证字段；
- 数据集边界明确；
- 不二次 Top N 裁剪；
- Item 可引用；
- 只有真实身份完整时才有 `available_actions`。

## 40.6 URL

- URL 不猜；
- 只接受两种验证来源；
- 缺失 URL 不污染 Evidence 状态；
- Report Agent 可直接使用已验证 URL。

---

# 41. 建议测试策略

## 41.1 离线测试

- Source ref 解析；
- `item_ref` Run-local 唯一；
- Manifest overall 确定性计算；
- Coverage 状态规则；
- Time shape exact mapping；
- Unsupported time blocked；
- Secret redaction；
- Request Record 原子写；
- Interrupted Run 冻结；
- stale inflight 检查；
- `runs.jsonl` 重建；
- schema_version Reader；
- Candidate all/top/filter；
- Sanitized Export。

## 41.2 Mock HTTP 测试

- Success；
- EMPTY；
- 4xx 不重试；
- transient failure + one retry；
- auth expired + one recovery；
- second auth expiry → fail；
- partial artifact；
- request intent persisted before response。

## 41.3 Live Validation

只做低风险、串行、固定时间的最小验证：

- discover；
- topology；
- performance；
- trace action；
- candidate source；
- verified URL。

---

# 42. 当前项目状态

可以直接进入：

```text
更新并冻结设计基线
↓
编写并执行单次 Codex Goal
↓
完整实现 v1
↓
离线测试
↓
最小、低风险 Live Validation
```

Candidate Dataset 主来源已经确定，不再存在实现前 Micro-Experiment Gate。

下一阶段最重要的是：

1. 保持本文档和 60 项决策文档为设计基线；
2. 先在文档和协议中回填 `request_overview` 作为 Candidate 主来源；
3. Codex 在一个 Goal 中完成完整设计收束、实现、测试和文档维护；
4. 实现过程中出现新问题，优先遵循既有决策，而不是临时发明新架构；
5. 只有确实无法从现有证据和仓库回答的问题才允许形成最小 `OPEN_QUESTION`，不得自行猜测。

---

# 43. 最终设计摘要

```text
听云 APM 新 CLI v1
不是 API Wrapper
不是报告生成器
不是自动诊断引擎

它是：

Agent-first
Evidence Package-first
Immutable Run-based
Read-only
Live-Verified
Low-pressure
Auditable
Branch-aware
URL-aware

的调查事实获取系统。
```

最终闭环：

```text
真实服务端
  ↓
不可变 Run
  ↓
Evidence Item
  ↓
available_actions
  ↓
Agent 选择
  ↓
Child Run
  ↓
调查经验自然沉淀
  ↓
独立 Agent 完成分析与报告
```

---

# 44. 2026-07-07 Runtime Contract Hardening 实现澄清

本节不改变前文设计历史，只记录 v1 Runtime 的落地约束：

- Runtime Stable Surface 仍锁定为 `investigate_trace` 与 `inspect_call_tree`，不新增 Action family。
- `live_request_count` 解释为实际发送并持久化的 raw request attempt 数；retry 与 auth replay 都会增加该计数。
- Preflight 使用 `expected_logical_request_count` 表示计划逻辑请求数；旧 `expected_live_request_count` 仅作为历史字段读取。
- Normalized Artifact 的 `derived_from` 指向最终支撑事实或失败判断的 raw response/error，而不是固定序号。
- `FAILED` 与 `EMPTY` 严格分离：HTTP/transport/business failure 是 `FAILED`，成功无域数据才是 `EMPTY`。
- Auth Recovery 为 Run-scoped，每个 Live Run 最多一次；transient retry 仅限网络瞬态异常与 HTTP 502/503/504。
- `available_actions` 必须满足 action-specific exact identity，且 `investigate` 发请求前会重新校验。`investigate_trace` 只使用 verified resolver：`WEB -> WEB`、`TX -> TX`、`BG -> BG`、`TX,IF -> TX`；未知 composite withheld。
- Trace proof 与 Navigation proof 分离；`BG` / `TX,IF` 的 Trace success 不自动产生内部 URL。
- 缺少 `TINGYUN_AUTHORIZATION` 的默认生产 Live command 在 HTTP 前阻断为 `BLOCKED / AUTH_NOT_CONFIGURED`。
- CLI startup 会冻结 confirmed stale `.inflight/` Run 为 `INTERRUPTED`，active owner PID 不冻结。
- Trace Detail 归一化提升 summary、timeline、trace-local topology、service flow、request service flow、exceptions、embedded stack 和 context，但不声称独立 `stackTraces` endpoint 已验证。
- Candidate verified URL 只从已验证 `/web/server/action/overview/{bizSystemId}/{applicationId}/{actionId}` route 和完整 identity 派生。
- 当前实现状态是 `Golden Path Live-Validated`，范围限定为已测试目标、时间窗口和 runtime version；不声明 Production-ready 或 all-domain Live-Proven。
