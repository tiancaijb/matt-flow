# 0002 — 结构化错误报告

**What to build:** 把 `_verify_implementation()` 从返回 `bool` 改成返回结构化错误，在 `cmd_run()` 中输出每个失败的详细原因。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 定义 `VerificationError` 类：`step: str`, `exit_code: int`, `stderr_summary: str`
- [ ] 重构 `_verify_implementation()` 返回 `list[VerificationError]`
- [ ] 在 `cmd_run()` 中捕获错误并逐行格式化输出：
  ```
  ❌ 验证失败 (ticket-NNNN):
     • TypeScript 类型检查 → 退出码 2
       src/cli.ts:42: error TS2322: Type 'string' is not assignable to type 'number'
  ```
- [ ] 在 `--status` 中显示最近一次失败的信息（从 `scratch/.last_error` 读取）
- [ ] 错误信息写入 `scratch/.last_error` 供跨 session 查看
