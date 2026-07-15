# auto-develop.py 单元测试 — 规格说明书

## Problem Statement

`auto-develop.py` 已有 token 估算、项目检测、错误报告等功能，但没有任何测试。每次修改都要手动验证，改坏了不知道。

## Solution

引入 pytest 测试框架，为核心函数编写单元测试，用 mock 文件模拟各种项目类型和 ticket 场景。

## User Stories

1. 作为维护者，我希望 `_estimate_tokens()` 有边界值测试（空字符串、纯文本、代码片段），以便确保 token 估算不会 crash
2. 作为维护者，我希望 `_detect_project_type()` 有 mock 文件测试（go.mod、Cargo.toml、pom.xml、package.json、pyproject.toml），以便确保项目检测逻辑正确
3. 作为维护者，我希望 `_get_completed_tickets()` 和 `_find_next_ticket()` 有 mock git log 测试，以便确保 ticket 进度追踪可靠
4. 作为维护者，我希望 `VerificationError` 的格式化输出测试，以便确保错误报告可读
5. 作为维护者，我希望 pytest 配置简单，不需要额外依赖（除了 pytest 本身）

## Implementation Decisions

### 测试框架

- 使用 `pytest`，不引入多余依赖
- 测试文件放在 `tests/test_auto_develop.py`
- 通过 `pyproject.toml` 配置 pytest（同时让 `_detect_project_type` 识别为 python 项目）

### 测试策略

- **Token 估算**: 直接调用函数，测试空字符串、1K/10K/100K 文本、代码片段
- **项目检测**: 在临时目录创建 mock 文件（go.mod、Cargo.toml 等），调用 `_detect_project_type()`
- **Ticket 解析**: 在临时目录创建 `scratch/tickets/NNNN-name.md`，模拟 git log，测试 `_find_next_ticket()`
- **错误格式化**: 直接构造 `VerificationError` 实例，测试 `__str__()` 输出格式
- **不测试**: 调 `pi` 子进程的函数（`_implement_ticket`、`_code_review`），这些需要集成测试

### 文件结构

```
pyproject.toml          # pytest 配置
tests/
  __init__.py
  test_auto_develop.py  # 主测试文件
```

## Testing Decisions

- 每个测试函数用一个 `def test_*`，独立可运行
- 临时文件用 `tmp_path` fixture（pytest 内置），不手动清理
- 测试不依赖网络、不调外部命令、不修改真实项目文件

## Out of Scope

- 不测试 `cmd_run()`、`cmd_status()` 等主流程函数（这些通过 --status 验证即可）
- 不添加 CI 测试运行（已有 CI 配置，后续可加 `pytest` 步骤）
- 不添加覆盖率工具

## Further Notes

- 本 spec 只覆盖已有功能的测试。新增功能时同步加测试
