---
name: matt-flow
description: >
  AI Coding Skills 工程工作流：Grill → Tickets → Auto-Implement → Re-Grill。
  规划阶段和你对话拆 ticket，实施阶段自动跑循环——找下一个未完成的 ticket、pi -p --no-session 实现、
  跑测试、git commit。失败重试 3 次后停。全部做完后叫你回来 re-grill。
argument-hint: "<project-dir>"
disable-model-invocation: false
---

# matt-flow — AI Coding Skills 工程工作流

Matt Pocock AI Coding Skills 的 pi 适配版。

## 用法

```bash
cd ~/dev/my-project
pi
# 进去后打 /matt-flow
```

或指定目录：`/matt-flow ~/dev/my-project`

## 项目初始化

首次使用 matt-flow 的项目需要初始化：

```bash
cd ~/dev/my-project
git init
# 如果已有代码
# git add -A && git commit -m "init"
```

matt-flow 靠 **git log** 判断哪些 ticket 已经完成了。
没有 git，自动循环不知道下一步做什么。

**项目目录结构约定：**

```
my-project/
├── scratch/
│   ├── SPEC.md          # 项目规格说明书（Phase 1 产出）
│   └── tickets/          # 拆好的 ticket 文件
│       ├── 0001-name.md
│       └── ...
├── scripts/
│   └── auto-develop.py   # Phase 2 自动生成
├── CONTEXT.md            # 项目背景档案（可选）
├── docs/
│   └── adr/              # 架构决策记录（可选）
└── .git/                 # 必须有
```

**如果没有 git，先 init 再走下一步。**

## 流程

### Phase 1: Grill（人参与 → 产出 tickets）

和你对话，把想法拆成可执行的 ticket。产出：

- `scratch/SPEC.md` — 项目规格说明书
- `scratch/tickets/NNNN-name.md` — 每个 ticket 一个文件
  - ticket 格式：**目标** + **背景** + **任务清单** + **产出标准** + **依赖**
- `docs/adr/` — 架构决策记录（可选）

**规则：**
- **逐点 grill**：每个问题单独问，等用户回答了再问下一个
- **grill 到底**：不能问两三个问题就开始写 ticket。直到所有开放问题都问完、用户明确认可（说"好"/"就这样"/"行"/"可以"），才算 grill 完成
- **不替用户做决定**：不给用户预设答案、不诱导选择。每个选项如实说明优缺点
- **不提前开跑**：grill 没完成之前，不能创建 ticket 文件、不能写代码、不能调任何工具
- 一次 grill 不一定要产出全部 ticket——只产当前阶段的（比如只 grill P0），剩下的下次再来

**Grill 自检清单（每次开始写 ticket 前必须过一遍）：**

- [ ] 所有开放问题都问过了？
- [ ] 每个问题用户都回答了？
- [ ] 用户明确说了"好"/"就这样"/"行"/"可以"来表示同意当前方案？
- [ ] 没有替用户做决定的选项？
- [ ] 没有跳过任何该问的设计细节？

如果以上有任何一项是❌，继续 grill，不能进入下一阶段。

Grill 完成后自动进入 Phase 2（不再询问，直接运行 auto-develop.py）。

### Phase 2: Auto-Implement（无人 → 自动运行）

先检查 `scripts/auto-develop.py` 是否存在。

**如果没有，根据项目类型生成一份：**

```bash
# 检测项目类型
# Python → pytest, python -m pytest
# Node → npm test / pnpm test
# 通用 → 问用户测试命令

# 写入 scripts/auto-develop.py
# 结构固定：
#   - 读 scratch/tickets/ → 查 git log 找未完成的
#   - pi -p --no-session @SPEC @ticket "实现这个 ticket"
#   - 跑测试
#   - 通过 → git commit -m "ticket-NNNN"
#   - 失败 → 重试 3 次 → 停
```

**如果有，直接运行：**

```bash
python3 scripts/auto-develop.py
```

脚本循环逻辑：

```
loop:
  1. 读 scratch/tickets/ 列出所有 ticket
  2. 查 git log → 跳过已提交的（commit message 含 ticket-NNNN）
  3. 找第一个未完成的 ticket
  4. pi -p --no-session @SPEC @ticket "实现这个 ticket"
  5. 跑测试（pytest / npm test / 用户指定的命令）
  6. ✅ 通过 → git commit -m "ticket-NNNN: name"
  7. ❌ 失败 → 重试 3 次 → 停住等你修
  8. 全部做完 → 打印总结 → 退出
```

**全自动完成或失败停下后，通知你回来看结果。**

### 归档 / 跳过 ticket

Grill 或 Re-Grill 阶段，想跳过某个 ticket（不删文件）：

> 用户："这个 ticket 先归档"
> 用户："跳过 ticket X"

在 ticket 文件第一行加 `status:` 标记，脚本自动忽略：

```markdown
# 0007: 标题

status: archived
```

| 标记 | 效果 |
|------|------|
| `status: archived` | 跳过，以后可以取消归档继续做 |
| `status: skipped` | 跳过，不打算做了 |
| `status: blocked` | 跳过，依赖未就绪 |
| （无标记） | 正常参与自动循环 |

**不需要你手动改文件**——Grill 阶段你只需说"归档"或"跳过"，我来改文件、提交。

### Phase 3: Re-Grill（人参与 → review + 下轮）

回到你这里：

1. Review 自动跑的成果
2. 修 bug（如果有失败的）
3. Grill 下一批 ticket
4. 回到 Phase 2

### 手动模式的备选

如果某个 ticket 太复杂不适合自动跑，可以手动开 session：

```bash
tmux new-window -n "feature-NNNN"
sleep 0.3
tmux send-keys -t "feature-NNNN" \
  "cd /path/to/project && \
   pi --name 'project/NNNN' \
      @scratch/SPEC.md \
      @scratch/tickets/NNNN-name.md \
      '实现这个 ticket'" C-m
```

但大多数情况自动跑就够了。

## 关键原则

1. **一次只 grill 当前阶段** — 不是非要把所有 ticket 都拆完才开跑，吃到哪做到哪
2. **自动实现靠 git log 判断进度** — 已提交的 ticket 跳过
3. **全自动失败后通知人** — 不闷着头无限重试
4. **不替用户做决定** — Phase 1 和 Phase 3 的每层决策问用户
5. **文件持久化上下文** — spec 和 tickets 写在文件里，自动跑时模型从文件读
6. **/resume 恢复** — 中途关闭用 `/resume` 恢复

## 误解预防（我的行为规范 — 必须逐条遵守）

以下规则在本 skill 读完后立即生效：

- [ ] 读完本文件后再行动，不边读边猜
- [ ] 先确认理解，等用户说"对"再继续
- [ ] **每问一句，等用户回答。用户没回之前，不能问下一句，不能写代码，不能创建文件**
- [ ] **grill 阶段禁止提前开跑**：用户说"好"之前，不创建 ticket 文件、不写代码、不调工具
- [ ] 遇到"下一步"时问用户，不替用户选方向
- [ ] 不主动读项目文件探状态——先问用户是否需要
- [ ] Grill 完成后自动进入 Phase 2（不询问）
- [ ] 如果用户说"继续开发 X"，问"按 matt-flow 来？先从 Grill 开始还是直接自动跑？"
- [ ] **用户指出跳过了 grill——立即停下，回到上一步，继续 grill 到完**
- [ ] **用户说"修改 skill"——优先做这件事，改完了再继续当前工作**

### 违反上述规则的后果

如果用户指出我违反了上述规则：
1. 立即停下手头一切工作
2. 承认错误，说清楚我跳过了哪一步
3. 回到跳过的步骤继续，不能再前进
