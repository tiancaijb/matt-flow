# matt-flow — 领域上下文

## 项目简介

matt-flow 是 Matt Pocock AI Coding Skills 的自动化编排工具。把 grill → spec → tickets → implement → code-review 串成自动循环，让 AI 自己写代码。

## 术语表

| 术语 | 定义 |
|------|------|
| Grill | Matt Pocock 的追问式需求调研，产出 CONTEXT.md |
| Spec | 规格说明书，存于 scratch/SPEC.md |
| Ticket | 一个 context window（~100K tokens）能装下的工作任务，存于 scratch/tickets/NNNN-name.md |
| Batch | 一批 ticket，对应一次 sprint |
| auto-develop.py | 自动开发循环脚本，遍历 ticket，调 pi 实现，验证，提交 |
| init-project.py | 项目脚手架，初始化 scratch/ 目录结构 |

## 当前迭代目标

完善 auto-develop.py，三个方向：
- A: 智能 ticket 工作量估算（token 估算，建议拆分）
- B: 更多项目类型支持（Go / Rust / Java）
- C: 更好的错误报告（结构化输出、详细原因）
