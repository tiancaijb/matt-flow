# matt-flow

AI 全自动开发工作流。你说需求，AI 自己拆任务、写代码、跑测试、提交。

**Grill → Tickets → Auto-Implement → Re-Grill**

Matt Pocock AI Coding Skills 的 pi 适配版。

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
3. 设置 API Key 环境变量（如 `DEEPSEEK_API_KEY`）
4. 进入项目目录，启动 pi，输入 `/matt-flow`

## 工作流

| 阶段 | 说明 |
|------|------|
| **Grill** | AI 追问你的需求细节，直到想清楚 |
| **Tickets** | AI 把项目拆成一个个可执行的任务 |
| **Auto-Implement** | 自动循环：找未完成的 ticket → 实现 → 跑测试 → 提交 |
| **Re-Grill** | 全部完成后叫你回来 review |

## 项目结构

```
my-project/
├── scratch/
│   ├── SPEC.md              # 项目规格说明书
│   └── tickets/              # 拆好的 ticket 文件
│       ├── 0001-name.md
│       └── ...
├── scripts/
│   └── auto-develop.py       # 自动开发循环脚本
├── CONTEXT.md                # 项目背景（可选）
└── docs/
    └── adr/                  # 架构决策记录（可选）
```

## 谁在用

matt-flow 已经在以下项目中跑通：

- **kdenlive-agent** — 视频编辑 AI Agent（30 tickets）
- **replyflow-mcp** — Twitter 回复管理 MCP 工具（13 tickets）
- **x-trail** — Twitter/X 线索阅读器（15+ tickets）
- **distroflow** — 引流帖生成 MCP 工具
- **obsidian-gtd** — Obsidian GTD 工作流
- **a-value-investing-skill** — A股价值投资分析 Skill

## License

MIT
