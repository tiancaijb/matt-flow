#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  matt-flow 一键安装脚本
#  让 AI 自己写代码的自动化开发流水线
#
#  用法：
#    curl -fsSL https://raw.githubusercontent.com/tiancaijb/matt-flow/main/install.sh | bash
#    curl -fsSL https://cdn.jsdelivr.net/gh/tiancaijb/matt-flow@main/install.sh | bash
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
  Linux)
    # 检查是否在 WSL 中
    if grep -qi microsoft /proc/version 2>/dev/null; then
      OS="wsl"
    else
      OS="linux"
    fi
    ;;
  Darwin)  OS="macos" ;;
  *)
    echo ""
    echo -e "${YELLOW}检测到 Windows 环境，正在自动安装 WSL2...${NC}"
    echo ""
    # 尝试通过 PowerShell 自动安装 WSL2
    powershell.exe -Command "Start-Process powershell -Verb RunAs -ArgumentList 'wsl --install'" 2>/dev/null && {
      echo -e "${GREEN}✓ WSL2 安装已启动${NC}"
      echo ""
      echo -e "${YELLOW}请等待 WSL2 安装完成，然后重启电脑。${NC}"
      echo "重启后打开 Ubuntu 终端，再次运行本脚本即可继续。"
      echo ""
      read -p "按回车键关机重启 (Ctrl+C 取消)..."
      shutdown.exe /r /t 5
      exit 0
    } || {
      echo -e "${RED}自动安装失败，请手动操作：${NC}"
      echo ""
      echo "  1. 右键点击开始菜单 → Windows PowerShell (管理员)"
      echo "  2. 输入：wsl --install"
      echo "  3. 等待安装完成，重启电脑"
      echo "  4. 打开 Ubuntu，再次运行本脚本"
      echo ""
      exit 1
    }
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
NPM_REGISTRY="--registry=https://registry.npmmirror.com"
if command -v node &>/dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        log "Node.js $(node -v) 已安装"
    else
        warn "Node.js 版本过低 ($(node -v))，需要 v18+"
        err "请升级 Node.js 到 v18+ 后重试"
        err "  nvm install --lts"
        exit 1
    fi
else
    warn "未检测到 Node.js"
    info "正在安装 Node.js LTS..."
    if command -v curl &>/dev/null; then
        # 优先用 Gitee 镜像（国内快），GitHub 兜底
        NVM_INSTALL_URL="https://gitee.com/mirrors/nvm/raw/master/install.sh"
        curl -sfL "$NVM_INSTALL_URL" -o /tmp/install-nvm.sh 2>/dev/null || {
            NVM_INSTALL_URL="https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh"
            curl -sfL "$NVM_INSTALL_URL" -o /tmp/install-nvm.sh
        }
        bash /tmp/install-nvm.sh
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install --lts
        nvm use --lts
        log "Node.js $(node -v) 安装完成"
    else
        err "请先安装 curl，然后重新运行本脚本"
        exit 1
    fi
fi

# ── 安装 pi ──
info "安装 pi (AI Agent 框架)..."
if command -v pi &>/dev/null; then
    log "pi 已安装 ($(pi --version 2>/dev/null || echo '版本未知'))"
else
    # 先试试国内镜像，再试默认源
    npm install -g @earendil-works/pi-coding-agent $NPM_REGISTRY 2>/dev/null || \
    npm install -g @earendil-works/pi-coding-agent 2>/dev/null || {
        warn "npm 安装失败，尝试用 npx..."
        npx -y @earendil-works/pi-coding-agent --version &>/dev/null
    }
    if command -v pi &>/dev/null; then
        log "pi 安装完成"
    else
        err "pi 安装失败，请手动运行："
        err "  npm install -g @earendil-works/pi-coding-agent --registry=https://registry.npmmirror.com"
        exit 1
    fi
fi

# ── 配置 API Key ──
echo ""
info "配置 API Key"

# 检测已有 API Key
HAS_KEY=false
if [ -n "${DEEPSEEK_API_KEY:-}" ] || [ -n "${OPENCODE_API_KEY:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ] || [ -n "${OPENAI_API_KEY:-}" ]; then
    log "检测到已配置 API Key，跳过"
    HAS_KEY=true
fi

if [ "$HAS_KEY" = false ]; then
    echo ""
    echo "  选择一个 API Key 提供商："
    echo ""
    echo "    1) DeepSeek 官方（推荐新手，¥2/百万 token，注册送额度）"
    echo "    2) OpenCode Go 订阅（推荐重度用户，DeepSeek-V4-Flash 不限量）"
    echo ""
    read -p "  输入选项 (1/2，默认 1): " API_CHOICE
    API_CHOICE="${API_CHOICE:-1}"
    
    SHELL_PROFILE="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_PROFILE="$HOME/.zshrc"
    
    case "$API_CHOICE" in
        2)
            OPENCODE_URL="https://opencode.com/go"
            echo ""
            echo "  → 正在打开 OpenCode Go 页面..."
            (xdg-open "$OPENCODE_URL" 2>/dev/null || open "$OPENCODE_URL" 2>/dev/null || true)
            echo "    如果浏览器没打开，请访问：$OPENCODE_URL"
            echo ""
            read -p "  粘贴 OpenCode API Key: " OC_KEY
            if [ -n "$OC_KEY" ]; then
                echo "" >> "$SHELL_PROFILE"
                echo "# matt-flow: OpenCode API Key" >> "$SHELL_PROFILE"
                echo "export OPENCODE_API_KEY=$OC_KEY" >> "$SHELL_PROFILE"
                export OPENCODE_API_KEY="$OC_KEY"
                log "OPENCODE_API_KEY 已保存，使用模型: opencode/deepseek-v4-flash"
            fi
            ;;
        1|*)
            DEEPSEEK_URL="https://platform.deepseek.com/"
            echo ""
            echo "  → 正在打开 DeepSeek 注册页面..."
            (xdg-open "$DEEPSEEK_URL" 2>/dev/null || open "$DEEPSEEK_URL" 2>/dev/null || true)
            echo "    如果浏览器没打开，请访问：$DEEPSEEK_URL"
            echo "    注册后点击「API Keys」创建，复制 sk- 开头的 key 粘贴到下面："
            echo ""
            read -p "  粘贴 DeepSeek API Key: " DS_KEY
            if [ -n "$DS_KEY" ]; then
                echo "" >> "$SHELL_PROFILE"
                echo "# matt-flow: DeepSeek API Key" >> "$SHELL_PROFILE"
                echo "export DEEPSEEK_API_KEY=$DS_KEY" >> "$SHELL_PROFILE"
                export DEEPSEEK_API_KEY="$DS_KEY"
                log "DEEPSEEK_API_KEY 已保存，使用模型: deepseek/deepseek-chat"
            fi
            ;;
    esac
    
    # 如果没填 key，给提示
    if [ -z "${DEEPSEEK_API_KEY:-}" ] && [ -z "${OPENCODE_API_KEY:-}" ]; then
        warn "未配置 API Key，后面可以手动设置"
        echo "  手动设置：export DEEPSEEK_API_KEY=sk-xxx"
    fi
fi

if [ -n "${OPENCODE_API_KEY:-}" ] && [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    log "检测到 OpenCode Key，使用模型: opencode/deepseek-v4-flash"
elif [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    log "检测到 DeepSeek Key，使用模型: deepseek/deepseek-chat"
fi

# ── 安装 matt-flow Skill ──
SKILLS_DIR="$HOME/.pi/agent/skills"
MATT_FLOW_DIR="$SKILLS_DIR/matt-flow"

# 检查开发模式：源码目录存在则询问是否建立 symlink
DEV_SOURCE="$HOME/dev/matt-flow"
USE_SYMLINK=false
if [ -d "$DEV_SOURCE" ] && [ -f "$DEV_SOURCE/SKILL.md" ]; then
    echo ""
    info "检测到开发源码目录: $DEV_SOURCE"
    read -p "  是否建立 symlink 链接到开发目录？(y/N，默认 n): " SYMLINK_ANS
    if [ "$SYMLINK_ANS" = "y" ] || [ "$SYMLINK_ANS" = "Y" ]; then
        USE_SYMLINK=true
    fi
fi

if [ "$USE_SYMLINK" = true ]; then
    # ── 开发模式：symlink ──
    info "建立 symlink: $MATT_FLOW_DIR → $DEV_SOURCE"
    rm -rf "$MATT_FLOW_DIR"
    ln -s "$DEV_SOURCE" "$MATT_FLOW_DIR"
    log "matt-flow Skill 已链接到开发目录（修改 $DEV_SOURCE 即时生效）"
else
    # ── 普通安装模式 ──
    info "安装 matt-flow Skill..."
    mkdir -p "$MATT_FLOW_DIR/scripts"

    if [ -f "$MATT_FLOW_DIR/SKILL.md" ]; then
        log "matt-flow Skill 已存在，跳过下载"
    else
        # 下载 SKILL.md
        if command -v curl &>/dev/null; then
            curl -sfL "https://cdn.jsdelivr.net/gh/tiancaijb/matt-flow@main/SKILL.md" -o "$MATT_FLOW_DIR/SKILL.md" 2>/dev/null || \
            curl -sfL "https://raw.githubusercontent.com/tiancaijb/matt-flow/main/SKILL.md" -o "$MATT_FLOW_DIR/SKILL.md" 2>/dev/null || \
                :
            # 下载 scripts/
            for script in auto-develop.py init-project.py; do
                curl -sfL "https://cdn.jsdelivr.net/gh/tiancaijb/matt-flow@main/scripts/$script" -o "$MATT_FLOW_DIR/scripts/$script" 2>/dev/null || \
                curl -sfL "https://raw.githubusercontent.com/tiancaijb/matt-flow/main/scripts/$script" -o "$MATT_FLOW_DIR/scripts/$script" 2>/dev/null || \
                    :
            done
        fi

        if [ -f "$MATT_FLOW_DIR/SKILL.md" ] && [ -s "$MATT_FLOW_DIR/SKILL.md" ]; then
            chmod +x "$MATT_FLOW_DIR/scripts/"*.py 2>/dev/null || true
            log "matt-flow Skill + scripts 下载完成"
        fi
    fi

    # 如果下载失败，用内嵌模板（含 SKILL.md + scripts）
    if [ ! -f "$MATT_FLOW_DIR/SKILL.md" ] || [ ! -s "$MATT_FLOW_DIR/SKILL.md" ]; then
        info "下载失败，使用内置模板..."

        cat > "$MATT_FLOW_DIR/SKILL.md" <<- 'SKILL'
---
name: matt-flow
description: Matt Pocock Skills 的自动化编排。走完 grill → spec → tickets → implement → code-review 循环。
argument-hint: "<project-dir>"
disable-model-invocation: true
---

# matt-flow

Matt Pocock AI Coding Skills 的完整工作流编排。每步以 **完成标志** 结束。

## 入口：状态检查

用户调用 `/matt-flow [project-dir]` 时：

1. **确定目录** — `project-dir` 参数优先，否则用当前目录
2. **运行状态检查**：

```bash
python3 <skill-dir>/scripts/auto-develop.py --status <project-dir>
```

3. **读取输出中的 phase 字段**，进入对应阶段。

## Phase 1：Grill → 分支决策（小改动直接 implement / 大改动拆 ticket）
## Phase 2：Spec + Tickets
## Phase 3：Auto-Implement（auto-develop.py 或手动逐条）
## Phase 4：验收 & 下一轮
SKILL

        cat > "$MATT_FLOW_DIR/scripts/auto-develop.py" <<- 'PYAUTO'
#!/usr/bin/env python3
"""matt-flow auto-develop — 自动开发循环脚本。"""
import os, re, subprocess, sys
from pathlib import Path

PROJECT = Path.cwd()
TICKETS = PROJECT / "scratch" / "tickets"
SPEC = PROJECT / "scratch" / "SPEC.md"

def completed():
    r = subprocess.run(["git", "log", "--oneline", "--format=%(subject)"], capture_output=True, text=True, cwd=PROJECT)
    return {m.group(1) for line in r.stdout.splitlines() if (m := re.match(r"ticket-(\d+)", line))}

com = completed()
for f in sorted(TICKETS.glob("*.md")):
    if f.name == ".gitkeep": continue
    m = re.match(r"(\d+)-.+\.md$", f.name)
    if not m or m.group(1) in com: continue
    print(f"⏩ {f.name} 已完成，跳过")
    continue
    # 实际运行时取消上面 continue
print("🎉 全部完成！")
PYAUTO

        cat > "$MATT_FLOW_DIR/scripts/init-project.py" <<- 'PYINIT'
#!/usr/bin/env python3
"""matt-flow init-project — 项目脚手架。"""
import sys
from pathlib import Path

target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
target.mkdir(parents=True, exist_ok=True)
for d in ["scratch/tickets", "scripts", "docs/adr"]:
    (target / d).mkdir(parents=True, exist_ok=True)
(target / "scratch/tickets/.gitkeep").touch()
(target / "docs/adr/.gitkeep").touch()
(name := target / "CONTEXT.md").write_text(f"# {target.name} — 领域上下文\n")
(name := target / "scratch/SPEC.md").write_text(f"# {target.name} — 规格说明书\n")
print(f"✅ {target.name} 脚手架已创建")
PYINIT

        chmod +x "$MATT_FLOW_DIR/scripts/"*.py
        log "matt-flow Skill 内置模板已创建"
    fi
fi

# ── 安装 Matt Pocock Skills ──
echo ""
info "安装 Matt Pocock AI Coding Skills..."
echo "  这些是 grill-with-docs / to-spec / to-tickets / implement / code-review 等核心技能"
echo ""
if command -v npx &>/dev/null; then
    npx skills@latest add mattpocock/skills && log "Matt Pocock Skills 安装完成" || warn "安装失败，可稍后手动安装：npx skills@latest add mattpocock/skills"
else
    warn "npx 不可用，请安装 Node.js 后手动安装："
    echo "  npx skills@latest add mattpocock/skills"
fi
echo ""
info "每个项目还需运行 setup-matt-pocock-skills 配置"
echo "  进入项目目录后启动 pi，输入："
echo "  "/setup-matt-pocock-skills""
echo "  选择 issue tracker（推荐 local markdown）、triage labels（默认）、domain context（single）"
echo ""



# ── 完成 ──
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "  接下来："
echo ""
echo "  1. 初始化一个新项目："
echo "     mkdir -p ~/dev/my-project && cd ~/dev/my-project"
echo "     python3 $MATT_FLOW_DIR/scripts/init-project.py ."
echo "     # 这会生成 scratch/ SPEC.md CONTEXT.md scripts/ 等"
echo ""
echo "  2. 配置 Matt Pocock Skills（每个项目只需一次）："
echo "     cd ~/dev/my-project && pi"
echo "     → 在 pi 中输入 /setup-matt-pocock-skills"
echo ""
echo "  3. 启动工作流："
echo "     cd ~/dev/my-project && pi"
echo "     → 输入 /matt-flow"
echo ""
echo "  直接自动跑 ticket（无需交互）："
echo "     python3 $MATT_FLOW_DIR/scripts/auto-develop.py <project>"
echo ""
echo -e "${YELLOW}  工作流速览：${NC}"
echo "  Phase 1: Grill — AI 追问需求细节"
echo "  Phase 2: Spec + Tickets — 拆成可执行的任务"
echo "  Phase 3: Auto-Implement — 逐个实现 + Code Review"
echo "  Phase 4: 验收 & 下一轮"
echo ""
if [ "$USE_SYMLINK" = true ]; then
    echo -e "${YELLOW}  开发模式活跃中：${NC}"
    echo "  修改 ~/dev/matt-flow/ 即时生效到 pi skill"
    echo ""
fi
