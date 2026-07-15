---
name: matt-flow
description: Matt Pocock Skills 的自动化编排。自动走完 grill → spec → tickets → implement 循环。
argument-hint: "<project-dir>"
disable-model-invocation: true
---

# matt-flow

Matt Pocock Skills 的自动化编排。把 grill → to-spec → to-tickets → implement + code-review 串成自动循环。

需要已安装 Matt Pocock Skills（`/setup-matt-pocock-skills` 装一次）。

## 用法

```bash
cd ~/dev/my-project
pi
/matt-flow
```

或：`/matt-flow ~/dev/my-project`

## 工作流

### Phase 1：Grill + Spec + Tickets

依次执行 Matt 的三个技能：

1. `/grill-with-docs` — 追问需求，产出 `CONTEXT.md`
2. `/to-spec` — 写出 `scratch/SPEC.md`
3. `/to-tickets` — 拆出 `scratch/tickets/` 下的 ticket 文件

**完成标志**：`scratch/tickets/` 下有 `.md` 文件。

### Phase 2：Auto-Implement

```bash
python3 scripts/auto-develop.py
```

脚本按顺序遍历 `scratch/tickets/`：
- 检查 git log 是否已有 `ticket-NNNN` 提交 → 有则跳过
- 无 → 调用 `/implement`（内部含 tdd + typecheck + test + code-review）
- `/implement` 通过 → git commit；失败 → 重试最多 3 次
- 全部 ticket 完成 → 回到你这里

**`/implement` 内部自动包含**：Matt 的 `/code-review` 双轴审查（对照 Spec + 对照代码标准 + Fowler 坏味道列表）。写代码和审代码由独立 sub-agent 完成，不共享上下文。

### Phase 3：Grill 下一批

回到你这里：

1. 验收当前 batch 的成果
2. 修失败 ticket（如有）
3. 决定继续 Grill 还是结束

继续 → 回到 Phase 1。没有新 ticket 了 → 结束。

## 原则

- **一次只 grill 当前阶段** — 不必拆完所有 ticket 才开跑
- **git log 判定进度** — 已提交的 ticket 自动跳过
- **失败通知人** — 重试 3 次仍失败就停
- **文件即记忆** — spec 和 tickets 写在文件里，跨 session 恢复
