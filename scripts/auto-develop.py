#!/usr/bin/env python3
"""
matt-flow auto-develop
======================
自动开发循环脚本。

用法：
  python3 <skill-dir>/scripts/auto-develop.py --status <project-dir>     检查项目状态
  python3 <skill-dir>/scripts/auto-develop.py --next <project-dir>       显示下一个未完成的 ticket
  python3 <skill-dir>/scripts/auto-develop.py <project-dir>              自动实现未完成的 tickets
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

MAX_RETRIES = 3


# ── 辅助函数 ─────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def _git_log(project: Path) -> list[str]:
    """Return commit subjects from git log."""
    result = _run(["git", "log", "--oneline", "--format=%(subject)"], project)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def _git_porcelain(project: Path) -> bool:
    """Return True if working tree is clean."""
    result = _run(["git", "status", "--porcelain"], project)
    return result.returncode == 0 and result.stdout.strip() == ""


def _get_completed_tickets(project: Path) -> set[str]:
    """Check git log for already committed tickets."""
    completed = set()
    for line in _git_log(project):
        m = re.match(r"ticket-(\d+)", line)
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
    completed = _get_completed_tickets(project) if state["has_git"] else set()
    all_tickets = _get_ticket_files(project)
    skipped = set()
    for tid, path in all_tickets:
        content = path.read_text()
        if "status: archived" in content or "status: skipped" in content:
            skipped.add(tid)

    state["total_tickets"] = len(all_tickets)
    state["completed_tickets"] = len(completed)
    state["skipped_tickets"] = len(skipped)
    state["pending_tickets"] = state["total_tickets"] - state["completed_tickets"] - state["skipped_tickets"]

    next_ticket = _find_next_ticket(project, completed)
    state["next_ticket_id"] = next_ticket[0] if next_ticket else None
    state["next_ticket_name"] = next_ticket[1].name if next_ticket else None
    state["next_ticket_path"] = str(next_ticket[1]) if next_ticket else None

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

    # Ticket detail
    if state["total_tickets"] > 0:
        completed = _get_completed_tickets(Path(state["project"]))
        for tid, path in _get_ticket_files(Path(state["project"])):
            content = path.read_text()
            if tid in completed:
                status = "DONE"
            elif "status: archived" in content or "status: skipped" in content:
                status = "SKIPPED"
            else:
                status = "PENDING"
            print(f"  {path.name} → {status}")
        print()

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


# ── 自动实现循环 ─────────────────────────────────────────

def cmd_run(project: Path):
    """Auto-implement loop."""
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
            all_pass = _verify_implementation(project)
            if not all_pass:
                print(f"❌ 验证未通过")
                continue

            # ── Commit ──
            _commit_ticket(tid, path)
            completed.add(tid)
            print(f"✅ ticket-{tid} 已提交")
            break
        else:
            print(f"\n❌ ticket-{tid} 重试 {MAX_RETRIES} 次均失败")
            print(f"   文件: {path}")
            print("   请手动检查后重试，或跳过：将 'status: skipped' 写入 ticket 文件头")
            sys.exit(1)

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


def _verify_implementation(project: Path) -> bool:
    """Run verification steps after implementation."""

    # TypeScript / Node projects
    if (project / "package.json").exists():
        for cmd in [
            ["npx", "tsc", "--noEmit"],
            ["npm", "run", "build"],
            ["npm", "test"],
        ]:
            result = _run(cmd, project)
            if result.returncode != 0:
                print(f"   验证失败: {' '.join(cmd)}")
                return False

    # Python projects
    if (project / "pyproject.toml").exists() or (project / "setup.py").exists():
        for cmd in [
            ["python3", "-m", "pytest", "-x", "-q"],
        ]:
            result = _run(cmd, project)
            if result.returncode != 0:
                print(f"   验证失败: {' '.join(cmd)}")
                return False

    # Git clean check
    if not _git_porcelain(project):
        print("   工作区有未提交文件（可能有新文件产生）")
        # This is expected after implementation — return True

    return True


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
    else:  # run
        cmd_run(project)


if __name__ == "__main__":
    main()
