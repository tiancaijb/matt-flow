# matt-flow 最终完善 — 规格说明书

## Problem Statement

matt-flow 核心功能已完整，但在几个边缘方面还有提升空间。

## Solution

四个方向并行完善：更多测试、install.sh 润色、Release 自动化、SKILL.md 精修。

## User Stories

1. 作为维护者，我希望 `cmd_status()` 和 `print_status()` 有测试覆盖，以便确保状态检查逻辑可靠
2. 作为维护者，我希望 `_verify_implementation()` 的返回值类型有测试覆盖，以便确保项目检测流程正确
3. 作为用户，我希望 `install.sh` 在 curl 下载失败时有更友好的回退提示，以便安装过程更顺畅
4. 作为用户，我希望 `install.sh` 检测到已安装的组件时提示更清晰，以便知道哪些步骤已跳过
5. 作为贡献者，我希望 push tag 时自动创建 GitHub Release，以便发布流程自动化
6. 作为用户，我希望 SKILL.md 按 writing-great-skills 原则修剪，去掉 no-op 和重复内容，以便更精准地指导 agent

## Out of Scope

- 不动 auto-develop.py 的核心逻辑
- 不动 install.sh 的安装流程架构（只改交互体验）

## Further Notes

- 四个方向独立，可以并行拆成 4 个 ticket
