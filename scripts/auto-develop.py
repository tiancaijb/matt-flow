#!/usr/bin/env python3
"""
matt-flow auto-develop
======================
自动开发循环脚本。

用法：
  python3 <skill-dir>/scripts/auto-develop.py --status <project-dir>     检查项目状态
  python3 <skill-dir>/scripts/auto-develop.py --next <project-dir>       显示下一个未完成的 ticket
  python3 <skill-dir>/scripts/auto-develop.py --run <project-dir>        自动实现（失败即退出）
  python3 <skill-dir>/scripts/auto-develop.py --run -y <project-dir>     跳过时间预估确认直接开跑
  python3 <skill-dir>/scripts/auto-develop.py --resume <project-dir>    自动实现（失败跳过，继续下一个）
  python3 <skill-dir>/scripts/auto-develop.py <project-dir>              等价于 --run
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

MAX_RETRIES = 3

# ── Token 估算（tiktoken 优先，回退到字符估算）──
try:
    import tiktoken
    _TOKENIZER = tiktoken.get_encoding("cl100k_base")
    def _estimate_tokens(text: str) -> int:
        return len(_TOKENIZER.encode(text))
except Exception:
    _TOKENIZER = None
    def _estimate_tokens(text: str) -> int:
        return int(len(text) / 3.5)

TOKEN_WARN = 100_000  # 警告阈值
TOKEN_LIMIT = 140_000  # 智能区上限


# ── 结构化错误 ───────────────────────────────────────────

class VerificationError:
    """A single verification step failure."""
    def __init__(self, step: str, exit_code: int, stderr_summary: str):
        self.step = step
        self.exit_code = exit_code
        self.stderr_summary = stderr_summary

    def __str__(self) -> str:
        return f"• {self.step} → 退出码 {self.exit_code}\n  {self.stderr_summary}"


LAST_ERROR_FILE = "scratch/.last_error"


def _read_last_error(project: Path) -> Optional[str]:
    """Read last error info from scratch/.last_error."""
    path = project / LAST_ERROR_FILE
    if path.exists():
        return path.read_text().strip()
    return None


def _write_last_error(project: Path, tid: str, errors: list):
    """Write last error info to scratch/.last_error."""
    path = project / LAST_ERROR_FILE
    lines = [f"ticket-{tid}:"]
    for err in errors:
        lines.append(f"  {err}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def _clear_last_error(project: Path):
    """Clear the last error file."""
    path = project / LAST_ERROR_FILE
    if path.exists():
        path.unlink()


# ── 辅助函数 ─────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def _git_log(project: Path) -> list[str]:
    """Return commit subjects from git log."""
    result = _run(["git", "log", "--oneline", "--format=%s"], project)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def _git_porcelain(project: Path) -> bool:
    """Return True if working tree is clean."""
    result = _run(["git", "status", "--porcelain"], project)
    return result.returncode == 0 and result.stdout.strip() == ""


def _get_completed_tickets(project: Path) -> set[str]:
    """Check git log for already committed tickets.
    Returns set of ticket IDs like '0001', '0002', etc.
    Only matches on the ticket-NNNN prefix, ignoring the descriptive text
    (which may use spaces/hyphens differently than filenames).
    """
    completed = set()
    for line in _git_log(project):
        m = re.match(r"ticket-(\d+):", line)
        if m:
            completed.add(m.group(1))
    return completed


def _get_ticket_files(project: Path) -> list[tuple[str, Path]]:
    """Return sorted list of (ticket_id, path) tuples from scratch/tickets/."""
    tickets_dir = project / "scratch" / "tickets"
    if not tickets_dir.exists():
        return []
    tickets = []
    for f in sorted(tickets_dir.glob("*.md")):
        if f.name == ".gitkeep":
            continue
        m = re.match(r"(\d+)-", f.stem)
        if m:
            tickets.append((m.group(1), f))
    return tickets


def _find_next_ticket(
    project: Path,
    completed: set[str],
) -> Optional[tuple[str, Path]]:
    """Find the first uncompleted ticket (skips archived/skipped ones)."""
    for tid, path in _get_ticket_files(project):
        if tid in completed:
            continue
        content = path.read_text()
        if "status: archived" in content or "status: skipped" in content:
            completed.add(tid)
            continue
        return (tid, path)
    return None


def _has_file(project: Path, *parts: str) -> bool:
    return (project / Path(*parts)).exists()


def _has_matt_setup(project: Path) -> bool:
    """Check if Matt's skills are configured (via .claude.md or CLAUDE.md)."""
    for fname in (".claude.md", "CLAUDE.md", ".cursorrules"):
        f = project / fname
        if f.exists() and "mattpocock" in f.read_text().lower():
            return True
    return False


# ── 状态检查 ──────────────────────────────────────────────

def cmd_status(project: Path) -> dict:
    """Check project state and return a structured dict."""
    state = {
        "project": str(project),
        "has_git": (project / ".git").exists(),
        "has_scratch": _has_file(project, "scratch"),
        "has_spec": _has_file(project, "scratch", "SPEC.md"),
        "has_tickets_dir": _has_file(project, "scratch", "tickets"),
        "has_context": _has_file(project, "CONTEXT.md"),
        "has_auto_develop": _has_file(project, "scripts", "auto-develop.py"),
        "has_matt_setup": _has_matt_setup(project),
        "git_clean": _git_porcelain(project) if (project / ".git").exists() else None,
    }

    # Tickets
    all_keys = _get_completed_tickets(project) if state["has_git"] else set()
    all_tickets = _get_ticket_files(project)
    skipped = set()
    # Match completed keys against current ticket files
    completed = set()
    for tid, path in all_tickets:
        if tid in all_keys:
            completed.add(tid)
        content = path.read_text()
        if "status: archived" in content or "status: skipped" in content:
            skipped.add(tid)

    state["total_tickets"] = len(all_tickets)
    state["completed_tickets"] = len(completed)
    state["skipped_tickets"] = len(skipped)
    state["pending_tickets"] = state["total_tickets"] - state["completed_tickets"] - state["skipped_tickets"]

    next_ticket = _find_next_ticket(project, all_keys)
    state["next_ticket_id"] = next_ticket[0] if next_ticket else None
    state["next_ticket_name"] = next_ticket[1].name if next_ticket else None
    state["next_ticket_path"] = str(next_ticket[1]) if next_ticket else None

    state["project_type"] = _detect_project_type(project) if state["has_scratch"] else "unknown"

    # Determine phase
    if not state["has_git"]:
        state["phase"] = "init"
    elif not state["has_scratch"] or state["total_tickets"] == 0:
        state["phase"] = "grill"
    elif state["pending_tickets"] > 0:
        state["phase"] = "implement"
    elif state["pending_tickets"] == 0 and state["total_tickets"] > 0:
        state["phase"] = "review"
    else:
        state["phase"] = "unknown"

    return state


def print_status(state: dict):
    """Pretty-print project state."""
    p = state["project"]
    print(f"=== matt-flow status: {p} ===")
    print()

    # Phase
    phase_labels = {
        "init": "新项目，需初始化",
        "grill": "待 Grill — 无 ticket",
        "implement": f"实现中 — 有 {state['pending_tickets']} 个 ticket 待完成",
        "review": "所有 ticket 已完成，待验收",
        "unknown": "状态不明",
    }
    print(f"Phase: {state['phase']}  ({phase_labels.get(state['phase'], '')})")
    ptype = state.get("project_type", "unknown")
    print(f"Project type: {ptype}")
    print()

    # Files
    checks = [
        ("git 仓库", state["has_git"]),
        ("scratch/", state["has_scratch"]),
        ("scratch/SPEC.md", state["has_spec"]),
        ("scratch/tickets/", state["has_tickets_dir"]),
        ("CONTEXT.md", state["has_context"]),
        ("scripts/auto-develop.py", state["has_auto_develop"]),
        ("Matt skills 已配置", state["has_matt_setup"]),
    ]
    for label, ok in checks:
        mark = "✓" if ok else "✗"
        print(f"  [{mark}] {label}")

    if state["has_git"]:
        clean = state["git_clean"]
        mark = "✓" if clean else "!"
        label = "工作区干净" if clean else "工作区有未提交修改"
        print(f"  [{mark}] {label}")

    print()
    print(f"Tickets:")
    print(f"  总计: {state['total_tickets']}")
    print(f"  已完成: {state['completed_tickets']}")
    print(f"  跳过: {state['skipped_tickets']}")
    print(f"  待办: {state['pending_tickets']}")
    if state["next_ticket_id"]:
        print(f"  下一个: {state['next_ticket_id']} — {state['next_ticket_name']}")
    else:
        print(f"  下一个: (无)")
    print()

    # Last error
    last_err = _read_last_error(Path(state["project"]))
    if last_err:
        print(f"最近错误:")
        print(f"  {last_err}")
        print()

    # Ticket detail with token estimates and time estimates
    if state["total_tickets"] > 0:
        completed_ids = _get_completed_tickets(Path(state["project"]))
        ticket_details = []
        for tid, path in _get_ticket_files(Path(state["project"])):
            content = path.read_text()
            if tid in completed_ids:
                status = "DONE"
            elif "status: archived" in content or "status: skipped" in content:
                status = "SKIPPED"
            else:
                status = "PENDING"
            
            tokens = _estimate_tokens(content)
            token_tag = ""
            if tokens > TOKEN_LIMIT:
                token_tag = " ⚠ OVER-LIMIT (>140K)"
            elif tokens > TOKEN_WARN:
                token_tag = " ⚠ OVERSIZED (>100K)"
            
            ticket_name = path.stem.split("-", 1)[1] if "-" in path.stem else path.stem
            type_name, weight = _detect_ticket_type(ticket_name)
            est_sec = _estimate_ticket_time(tokens, weight)
            
            ticket_details.append((path.name, status, tokens, token_tag, type_name, est_sec))
        
        for name, st, tokens, tag, ttype, est in ticket_details:
            if st == "PENDING":
                print(f"  {name} → {st}  ({tokens} tokens, {ttype}, ~{_format_duration(est)}){tag}")
            else:
                print(f"  {name} → {st}  ({tokens} tokens){tag}")
        print()
    else:
        print("  (no tickets yet)")

    # Guidance
    guidance = {
        "init": "运行 <skill-dir>/scripts/init-project.py <project> 初始化项目结构，或直接 /grill-with-docs",
        "grill": "进入 Phase 1：调用 /grill-with-docs",
        "implement": "进入 Phase 3：运行 auto-develop.py 或逐个实现 ticket",
        "review": "进入 Phase 4：验收成果，决定继续或结束",
        "unknown": "检查项目目录是否正确",
    }
    print(f"建议: {guidance.get(state['phase'], '')}")


def cmd_status_main(project: Path):
    state = cmd_status(project)
    print_status(state)
    return state


# ── 下一个 ticket ────────────────────────────────────────

def cmd_next(project: Path):
    completed = _get_completed_tickets(project)
    next_ticket = _find_next_ticket(project, completed)

    if not next_ticket:
        print("🎉 所有 ticket 已完成！")
        return

    tid, path = next_ticket
    spec_path = project / "scratch" / "SPEC.md"

    print(f"下一个: ticket-{tid}")
    print(f"  文件: {path}")
    if spec_path.exists():
        print(f"  Spec: {spec_path}")
    print()
    print(path.read_text())


# ── 时间预估 ─────────────────────────────────────────────

# Ticket 类型检测关键词（按文件名匹配）
_TICKET_TYPES: list[tuple[list[str], str, float]] = [
    (["test", "vitest"], "测试", 1.0),
    (["eslint", "config", "ci", "cd", "dependabot", "bump", "release", "workflow"], "配置/CI", 0.8),
    (["doc", "readme", "changelog", "contribut", "architecture", "license"], "文档", 0.7),
    (["perf", "optimize", "cache", "lazy", "render", "refresh", "debounce", "scan"], "性能", 1.3),
    (["refactor", "clean", "split", "extract"], "重构", 1.1),
]

# Token 量级 → 基础耗时（秒）
_BASE_ESTIMATE_TIERS: list[tuple[int, int]] = [
    (300, 180),     # < 300 tokens: 3 min
    (600, 240),     # < 600 tokens: 4 min
    (1000, 300),    # < 1000 tokens: 5 min
]

def _detect_ticket_type(ticket_name: str) -> tuple[str, float]:
    """Detect ticket type from filename. Returns (type_label, weight)."""
    name_lower = ticket_name.lower()
    for keywords, type_name, weight in _TICKET_TYPES:
        for kw in keywords:
            if kw in name_lower:
                return type_name, weight
    return "代码", 1.0


def _estimate_ticket_time(tokens: int, type_weight: float) -> int:
    """Estimate time in seconds for a single ticket."""
    for threshold, base_sec in _BASE_ESTIMATE_TIERS:
        if tokens < threshold:
            return max(60, int(base_sec * type_weight))
    return max(60, int(420 * type_weight))


def _format_duration(total_sec: int) -> str:
    """Format seconds to human readable duration string."""
    if total_sec >= 3600:
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        return f"{h}h{m}min" if m else f"{h}h"
    elif total_sec >= 120:
        return f"{total_sec // 60}min"
    elif total_sec >= 60:
        return f"1min"
    else:
        return f"{total_sec}s"


def _show_estimate(project: Path, completed: set[str]) -> int:
    """Display estimate table for pending tickets. Returns total estimate in seconds."""
    spec_path = project / "scratch" / "SPEC.md"
    spec_text = spec_path.read_text() if spec_path.exists() else ""
    spec_tokens = _estimate_tokens(spec_text)

    pending = []
    total_sec = 0
    for tid, path in _get_ticket_files(project):
        if tid in completed:
            continue
        content = path.read_text()
        if "status: archived" in content or "status: skipped" in content:
            continue
        tokens = _estimate_tokens(content) + spec_tokens
        ticket_name = path.stem.split("-", 1)[1] if "-" in path.stem else path.stem
        type_name, weight = _detect_ticket_type(ticket_name)
        est_sec = _estimate_ticket_time(tokens, weight)
        total_sec += est_sec
        pending.append((tid, ticket_name, type_name, tokens, est_sec))

    if not pending:
        return 0

    print()
    print(f"📊 本轮预估 ({len(pending)} tickets):")
    print(f"  {'ticket':<8} {'类型':<10} {'tokens':<8} 预估耗时")
    print(f"  {'-'*8} {'-'*10} {'-'*8} {'-'*8}")
    for tid, name, ttype, tokens, est in pending:
        print(f"  {tid:<8} {ttype:<10} {tokens:<8} {_format_duration(est)}")
    print(f"  {'-'*8} {'-'*10} {'-'*8} {'-'*8}")
    print(f"  {'':<8} {'':<10} {'合计':<8} {_format_duration(total_sec)}")
    print()
    return total_sec


# ── 自动实现循环 ─────────────────────────────────────────

def _check_ticket_sizes(project: Path, completed: set[str]):
    """Warn on tickets that exceed size thresholds."""
    spec_path = project / "scratch" / "SPEC.md"
    spec_text = spec_path.read_text() if spec_path.exists() else ""
    spec_tokens = _estimate_tokens(spec_text)

    for tid, path in _get_ticket_files(project):
        if tid in completed:
            continue
        content = path.read_text()
        total = _estimate_tokens(content) + spec_tokens
        if total > TOKEN_LIMIT:
            print(f"⚠  ticket-{tid} ({path.stem}) ~{total} tokens — 超出智能区上限 ({TOKEN_LIMIT})")
            print(f"   建议拆分后再运行")
        elif total > TOKEN_WARN:
            print(f"⚠  ticket-{tid} ({path.stem}) ~{total} tokens — 接近智能区上限")


def cmd_run(project: Path, resume: bool = False, auto_yes: bool = False):
    """Auto-implement loop.

    Args:
        project: Project directory.
        resume: If True, skip failed tickets and continue instead of exiting.
        auto_yes: If True, skip estimate confirmation.
    """
    os.chdir(str(project))

    # Check state first
    state = cmd_status(project)

    if state["phase"] == "init" or state["phase"] == "grill":
        print("⚠️  项目尚未准备好，请先完成 Phase 1 (Grill) 和 Phase 2 (Spec + Tickets)")
        return

    if state["phase"] == "review":
        print("🎉 所有 ticket 已完成！进入 Phase 4 验收。")
        return

    completed = _get_completed_tickets(project)
    spec_path = project / "scratch" / "SPEC.md"

    # Pre-check: warn on oversized tickets
    _check_ticket_sizes(project, completed)

    # Estimate (always show)
    total_est = _show_estimate(project, completed)
    if total_est == 0:
        print("🎉 没有待处理的 ticket")
        return

    # Confirm
    if not resume and not auto_yes:
        print("使用 --run -y 跳过预估确认直接开跑")
        sys.exit(0)

    failed_tickets = []

    while True:
        next_ticket = _find_next_ticket(project, completed)
        if not next_ticket:
            break

        tid, path = next_ticket
        ticket_name = path.stem

        print(f"\n{'='*60}")
        print(f"🚀 ticket-{tid}: {ticket_name}")
        print(f"{'='*60}")

        # ── Implement ──
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n🔄 第 {attempt} 次尝试...")

            success = _implement_ticket(project, spec_path, tid, path)
            if not success:
                print(f"❌ 第 {attempt} 次尝试失败")
                continue

            # ── Verify ──
            errors = _verify_implementation(project)
            if errors:
                print(f"❌ 验证失败 (ticket-{tid}):")
                for err in errors:
                    print(f"  {err}")
                _write_last_error(project, tid, errors)
                continue

            # ── Code Review ──
            review_errors = _code_review(project, spec_path, tid, path)
            if review_errors:
                print(f"❌ Code Review 未通过 (ticket-{tid}):")
                for err in review_errors:
                    print(f"  {err}")
                _write_last_error(project, tid, review_errors)
                continue

            # ── Commit ──
            _clear_last_error(project)
            _commit_ticket(tid, path)
            completed.add(tid)
            print(f"✅ ticket-{tid} 已提交")
            break
        else:
            print(f"\n❌ ticket-{tid} 重试 {MAX_RETRIES} 次均失败")
            print(f"   文件: {path}")
            _write_last_error(project, tid, [VerificationError("implement", -1, "重试 3 次均失败")])
            if resume:
                failed_tickets.append(tid)
                completed.add(tid)  # 标记为已完成（跳过），避免死循环
                print(f"   → 跳过，继续下一个 ticket (--resume 模式)")
            else:
                print("   请手动检查后重试，或跳过：将 'status: skipped' 写入 ticket 文件头")
                sys.exit(1)

    if failed_tickets:
        print(f"\n⚠️  以下 ticket 失败（已跳过）:")
        for tid in failed_tickets:
            print(f"  - ticket-{tid}")
        print(f" 修复后运行 --resume 继续")
    else:
        print(f"\n🎉 所有 ticket 已完成！")


def _implement_ticket(
    project: Path,
    spec_path: Path,
    tid: str,
    ticket_path: Path,
) -> bool:
    """Spawn pi to implement a single ticket."""
    cmd = ["pi", "-p", "--no-session"]

    if spec_path.exists():
        cmd.append(f"@{spec_path}")
    cmd.append(f"@{ticket_path}")
    cmd.append("实现这个 ticket，严格按照 SPEC.md 和 ticket 中的任务清单及验收标准执行")

    print(f"   执行: {' '.join(cmd[:3])} ...")
    result = _run(cmd, project)
    return result.returncode == 0


def _verify_implementation(project: Path) -> list:
    """Run verification steps after implementation. Returns list of VerificationError (empty = all pass)."""
    errors = []
    ptype = _detect_project_type(project)

    def _run_step(step_name: str, cmd: list[str]):
        """Run a single verification step, return VerificationError on failure or None."""
        # Skip if the tool is not available
        tool = cmd[0]
        if tool in ("go", "cargo", "mvn", "npx"):
            which_result = _run(["which", tool], project)
            if which_result.returncode != 0:
                errors.append(VerificationError(step_name, -1, f"{tool} 未安装，跳过"))
                return

        result = _run(cmd, project)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            lines = stderr.split("\n")
            if len(lines) > 3:
                stderr = "\n".join(lines[:3]) + f"\n  (... {len(lines)-3} more lines)"
            errors.append(VerificationError(step_name, result.returncode, stderr))

    verifiers = _LANG_VERIFIERS.get(ptype, [])
    for step_name, cmd in verifiers:
        _run_step(step_name, cmd)

    return errors


def _code_review(
    project: Path,
    spec_path: Path,
    tid: str,
    ticket_path: Path,
) -> list:
    """Run sub-agent code review: compare implementation against Spec + ticket.
    Returns list of VerificationError (empty = pass).
    """
    print(f"   🔍 Code Review 进行中...")

    # Build context: spec + ticket + git diff
    context_args = []
    if spec_path.exists():
        context_args.append(f"@{spec_path}")
    context_args.append(f"@{ticket_path}")

    # Add git diff if available
    diff_result = _run(["git", "diff", "HEAD", "--stat"], project)
    if diff_result.returncode == 0 and diff_result.stdout.strip():
        changed = diff_result.stdout.strip()
        context_args.append(f"已修改文件:\n{changed}")

    cmd = ["pi", "-p", "--no-session"] + context_args + [
        "对已实现的内容做 Code Review，从两个维度审查：",
        "1. Spec 维度：实现是否符合 SPEC.md 和 ticket 中的验收标准？",
        "2. 代码标准维度：代码有没有坏味道、风格问题、安全隐患？",
        "如果发现问题，列出具体问题和修改建议。如果没有问题，只输出 '✅ Code Review 通过'。"
    ]

    result = _run(cmd, project)
    if result.returncode != 0:
        return [VerificationError("Code Review", result.returncode,
                                   result.stderr.strip()[:200] or "子进程异常退出")]

    # Check if review explicitly passed
    output = result.stdout.strip()
    if "通过" in output or "pass" in output.lower():
        print(f"   ✅ Code Review 通过")
        return []

    # If output has substantial content, treat as review findings
    if len(output) > 20:
        return [VerificationError("Code Review", 1, output[:500])]

    return []


def _detect_project_type(project: Path) -> str:
    """Detect project type by checking for characteristic files.
    Returns one of: 'go', 'rust', 'java', 'node', 'python', 'unknown'.
    """
    checks = [
        ("go.mod", "go"),
        ("Cargo.toml", "rust"),
        ("pom.xml", "java"),
        ("package.json", "node"),
    ]
    for filename, ptype in checks:
        if (project / filename).exists():
            return ptype
    if (project / "pyproject.toml").exists() or (project / "setup.py").exists():
        return "python"
    return "unknown"


# ── 语言验证映射 ──

_LANG_VERIFIERS: dict[str, list[tuple[str, list[str]]]] = {
    "go": [
        ("Go vet", ["go", "vet", "./..."]),
        ("Go 测试", ["go", "test", "./..."]),
    ],
    "rust": [
        ("Rust cargo check", ["cargo", "check"]),
        ("Rust 测试", ["cargo", "test"]),
    ],
    "java": [
        ("Maven 测试", ["mvn", "test"]),
    ],
    "node": [
        ("TypeScript 类型检查", ["npx", "tsc", "--noEmit"]),
        ("构建", ["npm", "run", "build"]),
        ("测试套件", ["npm", "test"]),
    ],
    "python": [
        ("Python 测试", ["python3", "-m", "pytest", "-x", "-q"]),
    ],
}


def _commit_ticket(tid: str, path: Path):
    """Git commit the completed ticket."""
    ticket_name = path.stem.split("-", 1)[1] if "-" in path.stem else path.stem
    _run(["git", "add", "-A"], Path(path).parent.parent.parent)
    subprocess.run(
        ["git", "commit", "-m", f"ticket-{tid}: {ticket_name}"],
        cwd=Path(path).parent.parent.parent,
    )


# ── 入口 ──────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    mode = "run"
    auto_yes = False
    arg_idx = 1

    if sys.argv[1] == "--status":
        mode = "status"
        arg_idx = 2
    elif sys.argv[1] == "--next":
        mode = "next"
        arg_idx = 2
    elif sys.argv[1] == "--run":
        mode = "run"
        arg_idx = 2
        # Check for -y after --run
        if len(sys.argv) > 2 and sys.argv[2] == "-y":
            auto_yes = True
            arg_idx = 3
    elif sys.argv[1] == "-y":
        # -y before --run
        auto_yes = True
        mode = "run"
        arg_idx = 2
    elif sys.argv[1] == "--resume":
        mode = "resume"
        arg_idx = 2

    if arg_idx >= len(sys.argv):
        target = "."
    else:
        target = sys.argv[arg_idx]

    project = Path(target).resolve()

    if not project.is_dir():
        print(f"❌ {target} 不是目录")
        sys.exit(1)

    if mode == "status":
        cmd_status_main(project)
    elif mode == "next":
        cmd_next(project)
    elif mode == "resume":
        cmd_run(project, resume=True)
    else:  # run
        cmd_run(project, auto_yes=auto_yes)


if __name__ == "__main__":
    main()
