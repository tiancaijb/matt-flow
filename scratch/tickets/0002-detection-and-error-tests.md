# 0002 — 项目检测 + Ticket 解析 + 错误格式化测试

**What to build:** 测试 `_detect_project_type()`、`_get_completed_tickets()` / `_find_next_ticket()`、`VerificationError` 格式化。

**Blocked by:** 0001（测试基础设施）

**Status:** ready-for-agent

- [ ] 测试 `_detect_project_type()` 识别 go.mod / Cargo.toml / pom.xml / package.json / pyproject.toml
- [ ] 测试 `_detect_project_type()` 对空目录返回 "unknown"
- [ ] 测试 `_find_next_ticket()` 跳过已完成和已跳过的 ticket
- [ ] 测试 `_find_next_ticket()` 返回第一个未完成的 ticket
- [ ] 测试 `VerificationError.__str__()` 格式化输出包含步骤名和退出码
- [ ] 运行 `python3 -m pytest tests/ -v` 全部通过
