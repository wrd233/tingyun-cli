# Sanitized Export

Sanitized Export 是从 Internal Run 派生的安全交付副本，不是新 Run，不写 `runs.jsonl`，不访问服务端。

```bash
tingyun sanitized-export --run-id run-... --output .tingyun-runs/exports/run-safe
```

固定规则：

- 移除 Authorization、Cookie、Token、Password、Secret；
- 移除内部真实 Wire Identity；
- 移除本地绝对路径；
- 移除可执行 `available_actions`；
- 移除可点击内部 `links` / `url`；
- 清洗 error、attempt、raw summary 和 rich trace evidence 中可能承载的敏感字符串；
- 保留结构、类型、语义和证据血缘。

Sanitized Export 不能继续 `investigate`。需要继续调查时使用 Internal Run。

Sanitized Export 是交付副本，不写 `runs.jsonl`，不生成新的 Run，也不访问服务端。
