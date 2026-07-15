#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  matt-flow 一键安装脚本
#  让 AI 自己写代码的自动化开发流水线
#  用法：curl -fsSL https://raw.githubusercontent.com/wangy/matt-flow/main/install.sh | bash
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${BLUE}→${NC} $1"; }

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   matt-flow 一键安装脚本${NC}"
echo -e "${BLUE}   让 AI 自己写代码${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# ── 检测操作系统 ──
OS="$(uname -s)"
case "$OS" in
  Linux)   OS="linux" ;;
  Darwin)  OS="macos" ;;
  *)
    err "检测到 Windows 环境"
    err "本脚本需要在 WSL2（Linux 子系统）中运行"
    err ""
    err "请先在 PowerShell（管理员）中执行："
    err "  wsl --install"
    err "重启电脑后，打开 Ubuntu 终端，再运行本脚本"
    err ""
    err "Mac 用户可以直接运行本脚本，无需额外操作"
    exit 1
    ;;
esac
log "检测到操作系统: $OS"

# ── 检测架构 ──
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ARCH="x64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *)
    warn "未识别的架构: $ARCH，尝试继续..."
    ;;
esac

# ── 检测 Node.js ──
info "检查 Node.js..."
if command -v node &>/dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        log "Node.js $(node -v) 已安装"
    else
        warn "Node.js 版本过低 ($(node -v))，需要 v18+"
        info "推荐用 nvm 安装最新 LTS："
        info "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash"
        info "  nvm install --lts"
        exit 1
    fi
else
    warn "未检测到 Node.js"
    info "正在通过 nvm 安装 Node.js LTS..."
    if command -v curl &>/dev/null; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install --lts
        nvm use --lts
        log "Node.js $(node -v) 安装完成"
    else
        err "请先安装 curl，然后重新运行本脚本"
        err "  Ubuntu/Debian: sudo apt install curl"
        err "  macOS: 自带 curl"
        exit 1
    fi
fi

# ── 安装 pi ──
info "安装 pi (AI Agent 框架)..."
if command -v pi &>/dev/null; then
    log "pi 已安装 ($(pi --version 2>/dev/null || echo '版本未知'))"
else
    npm install -g @earendil-works/pi-coding-agent 2>/dev/null || {
        warn "npm 安装失败，尝试用 npx..."
        npx -y @earendil-works/pi-coding-agent --version &>/dev/null
    }
    if command -v pi &>/dev/null; then
        log "pi 安装完成"
    else
        err "pi 安装失败，请手动运行：npm install -g @earendil-works/pi-coding-agent"
        exit 1
    fi
fi

# ── 配置 API Key ──
echo ""
info "配置 API Key"
info "pi 通过环境变量读取 API Key，不需要配置文件"
echo ""
echo "  推荐方式（国内用户友好，便宜，无需翻墙）："
echo ""
echo "  【方案 A】DeepSeek 官方 API（推荐新手）"
echo "    价格：¥2/百万 token（约等于写 3 本《三体》）"
echo "    注册：https://platform.deepseek.com/"
echo "    充值 10 块钱能用非常久"
echo ""
echo "  【方案 B】OpenCode Go 订阅（推荐重度用户）"
echo "    包含 DeepSeek-V4-Flash，不限量调用"
echo "    订阅：https://opencode.com/go"
echo ""
echo "  其他选项（如果用 OpenAI 或 Anthropic）："
echo "    设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量即可"
echo ""

# 检测已有 API Key
deepseek_configured=false
opencode_configured=false

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    log "检测到已配置 DEEPSEEK_API_KEY"
    deepseek_configured=true
fi
if [ -n "${OPENCODE_API_KEY:-}" ]; then
    log "检测到已配置 OPENCODE_API_KEY"
    opencode_configured=true
fi

if [ "$deepseek_configured" = false ] && [ "$opencode_configured" = false ]; then
    echo "  请选择 API Key 方式："
    echo "    1) DeepSeek 官方 API（填 API Key）"
    echo "    2) OpenCode Go 订阅（填 API Key）"
    echo "    3) 两者都有（都填）"
    echo "    4) 跳过，我自己配"
    echo ""
    read -p "  输入选项 (1/2/3/4，默认 1): " API_CHOICE
    API_CHOICE="${API_CHOICE:-1}"
    
    SHELL_PROFILE="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_PROFILE="$HOME/.zshrc"
    
    case "$API_CHOICE" in
        1)
            read -p "  输入 DeepSeek API Key (sk-...): " DS_KEY
            if [ -n "$DS_KEY" ]; then
                echo "" >> "$SHELL_PROFILE"
                echo "# matt-flow: DeepSeek API Key" >> "$SHELL_PROFILE"
                echo "export DEEPSEEK_API_KEY=$DS_KEY" >> "$SHELL_PROFILE"
                export DEEPSEEK_API_KEY="$DS_KEY"
                log "DEEPSEEK_API_KEY 已写入 $SHELL_PROFILE"
                log "使用命令启动: pi --model deepseek/deepseek-chat"
            fi
            ;;
        2)
            read -p "  输入 OpenCode API Key: " OC_KEY
            if [ -n "$OC_KEY" ]; then
                echo "" >> "$SHELL_PROFILE"
                echo "# matt-flow: OpenCode API Key" >> "$SHELL_PROFILE"
                echo "export OPENCODE_API_KEY=$OC_KEY" >> "$SHELL_PROFILE"
                export OPENCODE_API_KEY="$OC_KEY"
                log "OPENCODE_API_KEY 已写入 $SHELL_PROFILE"
                log "使用命令启动: pi --model opencode/deepseek-v4-flash"
            fi
            ;;
        3)
            read -p "  输入 DeepSeek API Key (sk-...): " DS_KEY
            read -p "  输入 OpenCode API Key: " OC_KEY
            if [ -n "$DS_KEY" ]; then
                echo "" >> "$SHELL_PROFILE"
                echo "# matt-flow: API Keys" >> "$SHELL_PROFILE"
                echo "export DEEPSEEK_API_KEY=$DS_KEY" >> "$SHELL_PROFILE"
                export DEEPSEEK_API_KEY="$DS_KEY"
            fi
            if [ -n "$OC_KEY" ]; then
                echo "export OPENCODE_API_KEY=$OC_KEY" >> "$SHELL_PROFILE"
                export OPENCODE_API_KEY="$OC_KEY"
            fi
            log "API Key 已写入 $SHELL_PROFILE"
            ;;
        4)
            warn "跳过 API Key 配置，稍后手动设置"
            ;;
    esac
fi

# 保存默认模型选择到 pi 配置（通过别名或环境变量）
if [ -n "${OPENCODE_API_KEY:-}" ] && [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    log "推荐启动命令: pi --model opencode/deepseek-v4-flash"
elif [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    log "推荐启动命令: pi --model deepseek/deepseek-chat"
fi

# ── 安装 matt-flow Skill ──
info "安装 matt-flow Skill..."
SKILLS_DIR="$HOME/.pi/agent/skills"
MATT_FLOW_DIR="$SKILLS_DIR/matt-flow"
mkdir -p "$MATT_FLOW_DIR"

if [ -f "$MATT_FLOW_DIR/SKILL.md" ]; then
    log "matt-flow Skill 已存在，跳过下载"
else
    # 从 GitHub 下载（如果不可达则用本地模板）
    if command -v curl &>/dev/null; then
        curl -sfL "https://raw.githubusercontent.com/wangy/matt-flow/main/SKILL.md" -o "$MATT_FLOW_DIR/SKILL.md" 2>/dev/null && \
            log "matt-flow Skill 下载完成" || \
            warn "下载失败，使用内置模板"
    fi
    # 如果下载失败或者没有 curl，创建基本模板
    if [ ! -f "$MATT_FLOW_DIR/SKILL.md" ]; then
        cat > "$MATT_FLOW_DIR/SKILL.md" <<- 'SKILL'
---
name: matt-flow
description: >
  AI 全自动开发工作流：Grill → Tickets → Auto-Implement → Re-Grill。
  你说需求，AI 自己拆任务、写代码、跑测试、提交。
---

# matt-flow — AI 全自动开发工作流

## 用法
在 pi 对话中输入 `/matt-flow` 启动。

## 流程

### Phase 1: Grill
AI 追问你的需求细节，直到想清楚。

### Phase 2: Tickets
AI 把项目拆成一个个可执行的 Ticket 文件。

### Phase 3: Auto-Implement
自动循环：找未完成的 Ticket → 实现 → 跑测试 → 提交 → 下一个。

### Phase 4: Re-Grill
全部完成后叫你回来 review。
SKILL
        log "matt-flow Skill 模板已创建"
    fi
fi

# ── 创建 demo 项目 ──
DEMO_DIR="$HOME/dev/my-first-matt-flow-project"
if [ -d "$DEMO_DIR" ]; then
    warn "demo 项目目录已存在 ($DEMO_DIR)，跳过创建"
else
    info "创建 demo 项目..."
    mkdir -p "$DEMO_DIR/scratch/tickets"
    mkdir -p "$DEMO_DIR/scripts"
    
    cat > "$DEMO_DIR/scratch/SPEC.md" <<- 'SPEC'
# 项目规格说明书

## 项目名称
B站字幕提取工具

## 功能需求
1. 用户输入 B 站视频 BV 号
2. 脚本自动提取视频字幕
3. 输出为 TXT 文件（带时间戳分段）
4. 如果视频无字幕则提示用户

## 技术约束
- 使用 Python 3
- 依赖 bilibili-api-python
- CLI 交互
SPEC

    cat > "$DEMO_DIR/scripts/auto-develop.py" <<- 'PYTHON'
#!/usr/bin/env python3
"""
auto-develop — 自动开发循环脚本
"""
import subprocess, sys, time, re
from pathlib import Path

PROJECT = Path.cwd()
TICKETS = PROJECT / "scratch" / "tickets"
SPEC = PROJECT / "scratch" / "SPEC.md"
MAX_RETRIES = 3

ticket_re = re.compile(r"(\d{4})[-_](.+)\.md$")

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def has_commit(num):
    r = subprocess.run(["git", "log", "--oneline", "--grep", f"ticket-{num}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())

for f in sorted(TICKETS.iterdir()):
    m = ticket_re.match(f.name)
    if not m:
        continue
    num, name = m.group(1), m.group(2)
    if has_commit(num):
        log(f"⏩ ticket-{num} 已完成，跳过")
        continue
    log(f"▶ 实现 ticket-{num}: {name}")
    for attempt in range(1, MAX_RETRIES + 1):
        log(f"  尝试 {attempt}/{MAX_RETRIES}")
        r = subprocess.run(["pi", "-p", "--no-session",
                            str(SPEC), str(f), "实现这个 ticket"],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            log(f"  ⚠ 失败，{r.stderr[-200:] if r.stderr else ''}")
            time.sleep(5)
            continue
        r = subprocess.run(["python3", "-m", "pytest", "-x", "-q"],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            log(f"  ⚠ 测试失败，重试")
            time.sleep(5)
            continue
        subprocess.run(["git", "add", "-A"])
        subprocess.run(["git", "commit", "-m", f"ticket-{num}: {name}"])
        log(f"  ✅ ticket-{num} 完成")
        break
    else:
        log(f"⛔ ticket-{num} 失败，手动处理")
        sys.exit(1)

log("🎉 所有 Ticket 完成！")
PYTHON
    chmod +x "$DEMO_DIR/scripts/auto-develop.py"

    cd "$DEMO_DIR"
    git init
    git add -A
    git commit -m "init: matt-flow demo project"

    log "demo 项目已创建: $DEMO_DIR"
fi

# ── 完成 ──
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "  接下来："
echo ""
echo "  1. 进入 demo 项目："
echo "     cd $DEMO_DIR"
echo ""
echo "  2. 启动 pi："
echo "     pi"
echo ""
echo "  3. 在 pi 对话中输入 /matt-flow 启动工作流"
echo ""
echo "  或者直接自动跑："
echo "     cd $DEMO_DIR && python3 scripts/auto-develop.py"
echo ""
echo ""
echo -e "${YELLOW}  Windows 用户注意：${NC}"
echo "  本脚本需在 WSL2（Ubuntu）中运行，不是在 Windows cmd/PowerShell 里"
echo "  还没装 WSL2？管理员 PowerShell 里执行：wsl --install，重启即可"
echo ""
echo -e "${YELLOW}  首次使用提示：${NC}"
echo "  - 启动 /matt-flow 后，AI 会追问你需求细节（Grill 阶段）"
echo "  - 把需求说清楚后，AI 自动拆任务、写代码、测试、提交"
echo "  - demo 项目自带了一个示例需求，你也可以自己修改"
echo ""
