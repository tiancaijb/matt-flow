# 0001 — 更多测试覆盖

**What to build:** 为 `cmd_status()`、`_verify_implementation()` 等核心函数补充测试。

**Blocked by:** None — can start immediately.

**Status:** done

- [x] 测试 `_detect_project_type()` 集成到 `cmd_status()` 后的 state 包含 project_type 字段
- [x] 测试 `_verify_implementation()` 在无项目类型时返回空列表
- [x] 测试 `_verify_implementation()` 在 python 项目下运行 pytest
- [x] 运行 `python3 -m pytest tests/ -v` 全部通过
