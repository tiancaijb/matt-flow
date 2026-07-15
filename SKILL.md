---
name: matt-flow
description: Matt Pocock Skills 的自动化编排。走完 grill → spec → tickets → implement → code-review 循环。
argument-hint: "<project-dir>"
disable-model-invocation: true
---

# matt-flow

Matt Pocock AI Coding Skills 的完整工作流编排。每步以 **完成标志** 结束。

## 入口：状态检查

用户调用 `/matt-flow [project-dir]` 时运行状态检查：

```bash
python3 <skill-dir>/scripts/auto-develop.py --status <project-dir>
```

从输出中提取 `phase` 字段，进入对应阶段：

| phase | 含义 | 下一步 |
|-------|------|--------|
| `init` | 新项目，无 git / 无 scratch | 问用户是否 `init-project.py` 初始化 |
| `grill` | 无 tickets，需从需求开始 | 问用户是否先调 `/ask-matt` → 或直接 **Phase 1** |
| `implement` | 有 tickets 未完成 | **Phase 3** |
| `review` | 所有 ticket 已完成 | **Phase 4** |

状态检查也会列出已完成/待办的 ticket，每次走到入口时重新检查。

---

## Phase 1：Grill + 分支决策

### 步骤 1：Grill with Docs

调用 `/grill-with-docs` 追问需求，产出 `CONTEXT.md`（领域术语表）和可选 ADR。

**完成标志**：`CONTEXT.md` 存在且用户确认"理解了"。

### 步骤 2：分支决策

评估工作量：

- **小改动**（一个 **ticket** 能装下，~100K tokens）→ 直接调用 `/implement this`，跳到 **Phase 4**
- **大改动**（需多个 ticket）→ 进入 **Phase 2**

问用户确认分支选择。

**完成标志**：用户确认了分支。

---

## Phase 2：Spec + Tickets

### 步骤 3：to-spec

调用 `/to-spec`，产出 `scratch/SPEC.md`。

**完成标志**：`scratch/SPEC.md` 存在且内容完整（问题陈述 + 用户故事 + 验收标准 + 实施决策）。

### 步骤 4：to-tickets

调用 `/to-tickets`，将 spec 拆成多个 ticket，每个 ≈ 一个 context window（~100K tokens）。输出到 `scratch/tickets/NNNN-name.md`。

**完成标志**：`scratch/tickets/` 下有 `.md` 文件。

---

## Phase 3：Auto-Implement

两条路径，选一：

### 路径 A：自动（推荐）

```bash
python3 <skill-dir>/scripts/auto-develop.py <project-dir>
```

脚本行为：
1. 按顺序读取 `scratch/tickets/`
2. **git log** 检查是否已有 `ticket-NNNN` 提交 → 跳过已完成的
3. 未完成的 → 调 `pi` 加载 Spec + Ticket 上下文，实现 ticket
4. 跑项目类型检查/构建/测试
5. **调 `pi` 子进程做 Code Review**（双轴审查：对照 Spec + 对照代码标准）
6. 验证通过 → **git commit**；失败 → 重试最多 3 次
7. 继续下一个 ticket

**完成标志**：脚本退出码为 0，表示所有 ticket 已提交。

### 路径 B：手动（逐条实现）

自动脚本不适用时，逐条执行：

1. 加载 Spec + Ticket：
   ```
   @scratch/SPEC.md @scratch/tickets/NNNN-name.md
   实现这个 ticket，严格按照 SPEC.md 和 ticket 中的要求执行
   ```
2. 实现完成后，agent 自动包含 **Code Review**（sub-agent 双轴审查：对照 Spec + 对照代码标准）
3. 验证通过 → `git add -A && git commit -m "ticket-NNNN: name"`
4. 清空上下文，进入下一条 ticket

**完成标志**：所有 ticket 文件对应的 `ticket-NNNN` 提交出现在 git log 中。

---

## Phase 4：验收 & 下一轮

1. 向用户展示当前 batch 的成果
2. 如有失败 ticket，讨论修复方案
3. 问用户：**继续下一批还是结束？**
   - 继续 → 调 `/ask-matt` 获取下一批的方向建议，展示给用户，回到 **Phase 1**
   - 结束 → 完成

**完成标志**：用户确认结束，或继续下一轮 Grill。

---

## 原则

- **一次只 grill 当前阶段** — 拆完一个即可开跑下一个
- **git log 判定进度** — 已提交的 ticket 自动跳过
- **每个 ticket ≈ 一个 context window（~100K tokens）** — 确保 AI 输出质量
- **每次 ticket 后清空上下文** — 保持上下文清洁（手动路径关键）
- **失败通知人** — 重试 3 次仍失败则暂停，等人处理
- **文件即记忆** — spec 和 tickets 存于文件，跨 session 可恢复
