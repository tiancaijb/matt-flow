#!/usr/bin/env python3
"""
matt-flow init-project
=======================
为新项目搭建 scratch/ 工作目录结构。

用法：
  python3 <skill-dir>/scripts/init-project.py my-project
  python3 <skill-dir>/scripts/init-project.py .
"""

import os
import sys
import shutil
from pathlib import Path

SKILL_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent

TEMPLATES = {
    "CONTEXT.md": """# {project_name} — 领域上下文

## 项目简介

<!-- 在这里描述项目的核心目标 -->

## 术语表

| 术语 | 定义 |
|------|------|
|      |      |
""",
    "scratch/SPEC.md": """# {project_name} — 规格说明书

## 问题陈述

<!-- 要解决什么问题？ -->

## 用户故事

<!-- 用户如何使用这个系统？ -->

## 验收标准

<!-- 怎样才算完成？ -->

## 实施决策

<!-- 技术选型和架构决策 -->

""",
}


def init_project(project_dir: Path):
    """Create scaffold structure in project_dir."""
    project_name = project_dir.name

    # ── 创建目录结构 ──
    dirs = [
        "scratch/tickets",
        "scripts",
        "docs/adr",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # .gitkeep 占位
    (project_dir / "scratch/tickets/.gitkeep").touch()
    (project_dir / "docs/adr/.gitkeep").touch()

    # ── CONTEXT.md ──
    context_path = project_dir / "CONTEXT.md"
    if not context_path.exists():
        context_path.write_text(TEMPLATES["CONTEXT.md"].format(project_name=project_name))
        print(f"  ✓ CONTEXT.md")
    else:
        print(f"  · CONTEXT.md 已存在，跳过")

    # ── scratch/SPEC.md ──
    spec_path = project_dir / "scratch/SPEC.md"
    if not spec_path.exists():
        spec_path.write_text(TEMPLATES["scratch/SPEC.md"].format(project_name=project_name))
        print(f"  ✓ scratch/SPEC.md")
    else:
        print(f"  · scratch/SPEC.md 已存在，跳过")

    # ── scripts/auto-develop.py（从 skill 目录复制模板） ──
    template_path = SKILL_DIR / "scripts" / "auto-develop.py"
    dest_path = project_dir / "scripts" / "auto-develop.py"
    if template_path.exists():
        if not dest_path.exists():
            shutil.copy2(template_path, dest_path)
            dest_path.chmod(0o755)
            print(f"  ✓ scripts/auto-develop.py")
        else:
            print(f"  · scripts/auto-develop.py 已存在，跳过")
    else:
        print(f"  ⚠ auto-develop.py 模板未找到（{template_path}）")

    print(f"\n✅ {project_name} 脚手架已创建")
    print(f"   目录: {project_dir}")
    print(f"\n下一步：运行 /matt-flow 或 /grill-with-docs 开始")


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "."

    project_dir = Path(target).resolve()

    if not project_dir.exists():
        project_dir.mkdir(parents=True)

    if not project_dir.is_dir():
        print(f"❌ {target} 不是目录")
        sys.exit(1)

    print(f"🚧 搭建 {project_dir.name} 的项目脚手架...\n")
    init_project(project_dir)


if __name__ == "__main__":
    main()
