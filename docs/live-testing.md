# Live Testing

Codex 实现阶段默认不发真实听云请求。本仓库测试以 offline/mock 为主。

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

## 下一轮 Controlled Live Golden Path

本 hardening pass 不执行真实听云请求。下一轮由用户显式发起时，推荐顺序：

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
- Candidate metric 与 `available_actions` 身份门槛符合 contract；
- Trace normalized evidence 包含 summary、timeline、trace topology、service flow、exceptions、embedded stack 和 context；
- verified URL 只在完整 identity 和已验证 route 上出现；
- sanitized export 不含凭据、内部 identity、可执行 actions 或可点击内部 URL。
