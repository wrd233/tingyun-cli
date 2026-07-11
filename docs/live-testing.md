# Live Testing

Codex 实现阶段默认不发真实听云请求。本仓库测试以 offline/mock 为主。当前状态是 `Core Golden Path Live-Validated + Integrated Investigation Depth`，范围限定为已测试目标、时间窗口和 runtime version。

需要 Live Validation 时由用户显式发起，并应遵守：

- 使用低风险只读目标；
- 固定时间窗口；
- 请求数尽量少；
- 串行执行；
- 使用默认 2 秒 start-to-start 间隔；
- 确认 `preflight.json` 在第一条请求前冻结；
- 检查 Raw request/response 成对落盘；
- 检查无 Authorization、Cookie、Token 或内部敏感信息进入可提交文件。

历史微实验中的长间隔不等于 Runtime 默认。v1 默认间隔是 2 秒。

## Controlled Live Golden Path Shape

本 closure pass 不执行真实听云请求。已验证 Golden Path 的运行形状为：

本 branch integration 同样执行 0 次 Live Tingyun 请求。Advanced Source 只通过 synthetic fixtures、fake transport 和既有协议证据验证，因此不得把它们写成 Live-Proven。未来如显式开展 source live validation，应逐能力、一次一个 recipe 记录实际 shape；不能用 responseList 的成功 lineage 泛化 errorList/throughtList。

```text
discover              -> 1 logical request
collect               -> topology / performance / candidates
inspect candidates    -> 0 requests
investigate_trace     -> 1 logical request
inspect_call_tree     -> 1 logical request
```

所有真实请求保持串行，最大 in-flight 为 1，默认 start-to-start 间隔不少于 2 秒。

Live 验收时逐项检查：

- `preflight.json` 在第一条 live request 前冻结；
- raw request/response/error 与 `live_request_count` 一致；
- retry/auth replay 后 Artifact `derived_from` 指向最终支撑 raw ref；
- `coverage.json` 包含 attempt、retry、auth metadata；
- Candidate metric 与 `available_actions` 身份门槛符合 contract，`error_rate` 使用 percent 数值；
- Trace actionType 只使用已验证 semantic-kind + requestType 映射：Web+WEB -> WEB、Web+TX -> TX、Background+BG -> BG、Web+TX,IF -> TX；
- Trace normalized evidence 包含 summary、timeline、trace topology、service flow、exceptions、embedded stack 和 context；
- verified URL 只在完整 identity 和独立 route proof 上出现；Trace proof 不自动产生 Navigation proof；
- sanitized export 不含凭据、内部 identity、可执行 actions 或可点击内部 URL。
