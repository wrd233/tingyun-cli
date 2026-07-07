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
