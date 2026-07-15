# matt-flow

AI 全自动开发工作流。你说需求，AI 自己拆任务、写代码、跑测试、提交。

**Grill → Spec + Tickets → Auto-Implement → Review**

Matt Pocock AI Coding Skills 的 pi 适配版。把 `grill-with-docs` → `to-spec` → `to-tickets` → `implement` → `code-review` 串成自动循环，让 AI 自己写代码。

---

## 快速开始

```bash
# 1. 一键安装（见下方安装说明）
curl -fsSL https://raw.githubusercontent.com/tiancaijb/matt-flow/main/install.sh | bash

# 2. 初始化项目
mkdir -p ~/dev/my-project && cd ~/dev/my-project
python3 ~/.pi/agent/skills/matt-flow/scripts/init-project.py .

# 3. 启动工作流
cd ~/dev/my-project && pi
# 在 pi 对话中输入 /matt-flow
```

> **直接开跑**：已有 `scratch/SPEC.md` 和 tickets？
> ```bash
> python3 ~/.pi/agent/skills/matt-flow/scripts/auto-develop.py .
> ```

---

## 一行命令安装

```bash
curl -fsSL https://raw.githubusercontent.com/tiancaijb/matt-flow/main/install.sh | bash
```

安装完成后：

```bash
cd ~/dev/my-first-matt-flow-project
pi --model deepseek/deepseek-chat
```

在 pi 对话中输入 `/matt-flow` 启动。

## 手动安装

1. 安装 [pi](https://github.com/earendil-works/pi-coding-agent)
2. 把 `SKILL.md` 放到 `~/.pi/agent/skills/matt-flow/`
3. 将 `scripts/` 目录也复制到 `~/.pi/agent/skills/matt-flow/scripts/`
4. 设置 API Key 环境变量（如 `DEEPSEEK_API_KEY`）
5. 进入项目目录，启动 pi，输入 `/matt-flow`

---

## 工作流

matt-flow 把 AI 开发拆成 4 个阶段，由 `/matt-flow` 入口自动检测当前进度：

| Phase | 名称 | 说明 | 入口 |
|-------|------|------|------|
| **1** | **Grill + 分支决策** | AI 追问需求细节，产出领域术语表。小改动直接实现，大改动进入 Phase 2 | `/grill-with-docs` → 分支判断 |
| **2** | **Spec + Tickets** | 产出规格说明书 `scratch/SPEC.md`，拆成多个 ticket（每 ticket ≈ 一个 context window） | `/to-spec` → `/to-tickets` |
| **3** | **Auto-Implement** | 自动循环：找未完成的 ticket → 调 pi 实现 → 跑类型检查/测试 → 验证通过后 git commit | `auto-develop.py` 或手动逐条 |
| **4** | **验收 & 下一轮** | 展示成果，处理失败 ticket，决定继续还是结束 | 手动确认 |

### 状态检测

每次调用 `/matt-flow` 自动检测项目处于哪个阶段：

| phase | 含义 | 下一步 |
|-------|------|--------|
| `init` | 新项目，无 git / 无 scratch | 运行 `init-project.py` 初始化 |
| `grill` | 无 tickets，需从需求开始 | 进入 **Phase 1** |
| `implement` | 有 tickets 未完成 | 进入 **Phase 3** |
| `review` | 所有 ticket 已完成 | 进入 **Phase 4** |

---

## 脚本说明

### `init-project.py` — 项目脚手架

为项目搭建 `scratch/` 工作目录结构：

```bash
# 在当前目录初始化
python3 <skill-dir>/scripts/init-project.py .

# 创建新项目
python3 <skill-dir>/scripts/init-project.py my-project
```

生成的文件：
- `CONTEXT.md` — 项目领域上下文模板
- `scratch/SPEC.md` — 规格说明书模板
- `scratch/tickets/` — ticket 目录（含 `.gitkeep`）
- `scripts/auto-develop.py` — 自动开发脚本（从 skill 目录复制）
- `docs/adr/` — 架构决策记录目录

### `auto-develop.py` — 自动开发循环

遍历未完成的 tickets，自动实现、验证、提交：

```bash
# 查看项目状态
python3 <skill-dir>/scripts/auto-develop.py --status <project>

# 查看下一个未完成的 ticket
python3 <skill-dir>/scripts/auto-develop.py --next <project>

# 启动自动开发循环
python3 <skill-dir>/scripts/auto-develop.py <project>
```

脚本行为：
1. 按顺序读取 `scratch/tickets/`
2. 从 **git log** 识别已完成的 ticket（按 `ticket-NNNN` 提交信息匹配），跳过
3. 未完成的 → 调 `pi` 加载 Spec + Ticket 上下文，实现 ticket
4. 按项目类型（Go / Rust / Java / Node / Python）运行对应验证
5. 验证通过 → `git commit`；失败 → 重试最多 3 次
6. 继续下一个 ticket

---

## 项目结构

```
my-project/
├── scratch/
│   ├── SPEC.md              # 项目规格说明书
│   ├── tickets/              # 拆好的 ticket 文件
│   │   ├── 0001-name.md
│   │   └── ...
│   └── .last_error           # 最近错误记录（自动生成）
├── scripts/
│   └── auto-develop.py       # 自动开发循环脚本
├── CONTEXT.md                # 项目背景与领域术语表
├── docs/
│   └── adr/                  # 架构决策记录（可选）
└── .claude.md 或 CLAUDE.md   # Matt Pocock Skills 配置
```

### Skill 目录结构

```
~/.pi/agent/skills/matt-flow/
├── SKILL.md                  # matt-flow Skill 定义
└── scripts/
    ├── auto-develop.py       # 自动开发循环
    └── init-project.py        # 项目脚手架
```

---

## 谁在用

matt-flow 已经在以下项目中跑通：

- **kdenlive-agent** — 视频编辑 AI Agent（30 tickets）
- **replyflow-mcp** — Twitter 回复管理 MCP 工具（13 tickets）
- **x-trail** — Twitter/X 线索阅读器（15+ tickets）
- **distroflow** — 引流帖生成 MCP 工具
- **obsidian-gtd** — Obsidian GTD 工作流
- **a-value-investing-skill** — A股价值投资分析 Skill

---

## License

MIT
