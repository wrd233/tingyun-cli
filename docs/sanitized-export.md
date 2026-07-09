# Sanitized Export

Sanitized Export 是从 Internal Run 派生的 identity-sanitized external handoff，不是新 Run，不写 `runs.jsonl`，不访问服务端。它不是 secret-stripped raw copy，也不能作为 continuation source。

```bash
tingyun sanitized-export --run-id run-... --output .tingyun-runs/exports/run-safe
```

固定规则：

- 移除 Authorization、Cookie、Token、Password、Secret；
- 移除内部真实 Wire Identity；
- 使用一个共享 pseudonym state 处理整个 export，同一原始身份在 manifest、coverage、evidence 和 safe raw request metadata 中得到同一 pseudonym；
- 清洗数组、嵌套值和 composite strings 中已知 identity token，但保留普通 metric number；
- 移除本地绝对路径；
- 移除可执行 `available_actions`；
- 移除可点击内部 `links` / `url`；
- 默认排除任意 Raw response body；只允许经过清洗的 safe request metadata；
- 清洗 error、attempt、raw summary 和 rich trace evidence 中可能承载的敏感字符串；
- 保留结构、类型、语义和证据血缘。

Sanitized Export 不能继续 `investigate`。需要继续调查时使用 Internal Run。

Sanitized Export 是交付副本，不写 `runs.jsonl`，不生成新的 Run，也不访问服务端。
