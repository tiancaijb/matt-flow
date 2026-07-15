# 0001 — 测试基础设施 + Token 估算测试

**What to build:** 初始化 pytest 配置，编写 `_estimate_tokens()` 的边界值测试。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 创建 `pyproject.toml` 配置 pytest
- [ ] 创建 `tests/__init__.py` 和 `tests/test_auto_develop.py`
- [ ] 测试 `_estimate_tokens("")` 返回 0
- [ ] 测试 `_estimate_tokens()` 对纯文本和代码片段不 crash
- [ ] 测试 `_estimate_tokens()` 对 1K/10K/100K 文本返回合理值
- [ ] 运行 `python3 -m pytest tests/ -v` 全部通过
