# matt-flow CI/CD & 文档 — 规格说明书

## Problem Statement

matt-flow 作为一个开源工具，目前缺少自动化测试和规范的文档，导致：
1. install.sh 没有 CI 验证，改坏了不知道
2. 新用户看到 `~/dev/matt-flow/README.md` 还是旧的描述，与实际工作流脱节
3. 开发者贡献代码没有测试保障

## Solution

给 matt-flow 加上 GitHub Actions CI 和更新的 README，让新用户开箱即用、贡献者有安全感。

## User Stories

1. 作为维护者，我希望每次 push 到 main 或 PR 时自动运行 install.sh 语法检查和 lint，以便及早发现问题
2. 作为维护者，我希望 CI 验证 `init-project.py` 和 `auto-develop.py` 能正常导入和执行，以便确保脚本可运行
3. 作为新用户，我希望 README 描述当前的实际工作流（状态检查 → grill → spec → tickets → implement → code-review），以便知道怎么用
4. 作为新用户，我希望 README 有安装步骤、使用示例和项目结构说明，以便快速上手
5. 作为开发者，我希望 CI 配置简洁易维护，以便后续扩展

## Implementation Decisions

### CI/CD（GitHub Actions）

- 单文件 `.github/workflows/ci.yml`
- 触发条件：push 到 main + pull request
- 步骤：
  1. checkout
  2. shellcheck 检查 install.sh
  3. Python 语法检查（`python3 -m py_compile scripts/*.py`）
  4. 运行 `python3 scripts/auto-develop.py --help` 验证入口
  5. 运行 `python3 scripts/auto-develop.py --status .` 验证状态检查不 crash
- 不在此 ticket 范围：npm 发布、自动部署

### README 更新

- 保留原有的项目定位和安装方式
- 更新工作流描述为当前实际流程
- 增加 `init-project.py` 使用说明
- 增加项目结构图
- 增加"直接开跑"快速路径

## Testing Decisions

- CI 配置本身不需要测试，但需要验证语法正确
- README 不需要测试

## Out of Scope

- 不添加单元测试框架（pytest 等）
- 不添加集成测试

## Further Notes

- CI 使用 ubuntu-latest 运行
- Python 3.10+ 即可
