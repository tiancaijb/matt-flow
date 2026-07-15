# 0001 — Token 估算

**What to build:** auto-develop.py 在读取 ticket 时估算其 token 数，在 `--status` 输出中显示，对超出 ~100K tokens 的 ticket 发出警告。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 实现 `_estimate_tokens(text: str) -> int` 函数
  - 优先使用 `tiktoken` 库（`cl100k_base` 编码）
  - 回退到 `len(text) / 3.5` 简单估算
- [ ] 在 `cmd_status()` / `print_status()` 中为每个 ticket 显示 token 估算值
- [ ] 在状态输出中标记超出 100K tokens 的 ticket 为 `⚠ OVERSIZED`
- [ ] 在 `cmd_run()` 预处理阶段检查 ticket 大小，超出 140K 时警告但不阻止执行
- [ ] `tiktoken` 缺失时不 crash，静默回退到简单估算
