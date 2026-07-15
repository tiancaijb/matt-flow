"""
Tests for scripts/auto-develop.py — token estimation, project detection,
ticket parsing, error formatting.

This test file uses importlib to load auto-develop.py (hyphenated
filename prevents regular import).  See SPEC.md for full strategy.
"""

import importlib.util
from pathlib import Path

import pytest

# ── Load the module once ──────────────────────────────────────

_SCRIPT = str(Path(__file__).resolve().parents[1] / "scripts" / "auto-develop.py")

_spec = importlib.util.spec_from_file_location("auto_develop", _SCRIPT)
if _spec is None:
    raise ImportError(f"Cannot load spec from {_SCRIPT} — file may be missing")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_estimate_tokens = _mod._estimate_tokens
_detect_project_type = _mod._detect_project_type
_find_next_ticket = _mod._find_next_ticket
cmd_status = _mod.cmd_status
_verify_implementation = _mod._verify_implementation
VerificationError = _mod.VerificationError


# ── Tests ──────────────────────────────────────────────────────

class TestEstimateTokens:
    """_estimate_tokens() 边界值与合理性测试"""

    def test_empty_string_returns_zero(self):
        """空字符串应返回 0 token"""
        assert _estimate_tokens("") == 0

    def test_short_text_positive(self):
        """短文本应返回合理的 token 数"""
        tokens = _estimate_tokens("Hello, world!")
        assert 1 < tokens < 20, f"Expected 1–20 tokens, got {tokens}"

    def test_chinese_text(self):
        """中文文本返回合理的 token 数"""
        tokens = _estimate_tokens("你好世界")
        assert 1 < tokens < 20, f"Expected 1–20 tokens, got {tokens}"

    def test_mixed_text(self):
        """中英文混排返回合理的 token 数"""
        text = "Hello 你好 world 世界 foo bar baz"
        tokens = _estimate_tokens(text)
        assert 1 < tokens < 30, f"Expected 1–30 tokens, got {tokens}"

    def test_code_snippet(self):
        """Python 代码片段返回合理的 token 数"""
        code = '''
def hello(name: str) -> None:
    """Greet someone."""
    print(f"Hello, {name}!")


if __name__ == "__main__":
    hello("world")
'''
        tokens = _estimate_tokens(code)
        assert 5 < tokens < 100, f"Expected 5–100 tokens, got {tokens}"

    def test_code_snippet_go(self):
        """Go 代码片段返回合理的 token 数"""
        code = '''
package main

import "fmt"

func main() {
    fmt.Println("Hello, world!")
}
'''
        tokens = _estimate_tokens(code)
        assert 5 < tokens < 80, f"Expected 5–80 tokens, got {tokens}"

    def test_code_snippet_javascript(self):
        """JavaScript 代码片段返回合理的 token 数"""
        code = '''
function greet(name) {
    console.log(`Hello, ${name}!`);
}

module.exports = { greet };
'''
        tokens = _estimate_tokens(code)
        assert 5 < tokens < 80, f"Expected 5–80 tokens, got {tokens}"

    def test_token_count_1k_chars(self):
        """~770 字符的文本返回合理 token 数"""
        text = "Hello world! " * 55  # 14 × 55 = 770 chars
        tokens = _estimate_tokens(text)
        assert 50 < tokens < 500, f"Expected 50–500 for ~770 chars, got {tokens}"

    def test_token_count_10k_chars(self):
        """~10K 字符的文本返回合理 token 数"""
        text = "Hello world! This is a test sentence with some variety. " * 200  # ~10K
        tokens = _estimate_tokens(text)
        assert 500 < tokens < 5_000, f"Expected 500–5K for ~10K chars, got {tokens}"

    def test_token_count_100k_chars(self):
        """~90K 字符的文本返回合理 token 数"""
        line = "The quick brown fox jumps over the lazy dog. "
        text = line * 2000  # ~90K chars
        tokens = _estimate_tokens(text)
        # cl100k_base for English text: ~1 token per 2-3 chars
        assert 20_000 < tokens < 50_000, f"Expected 20K–50K for ~90K chars, got {tokens}"

    def test_newlines_only(self):
        """只有换行符的文本应返回 0 或少量 token"""
        tokens = _estimate_tokens("\n\n\n\n")
        # tiktoken may tokenize newlines as bytes; accept 0 or a small positive
        assert 0 <= tokens < 20, f"Expected 0–20 tokens for newlines, got {tokens}"

    def test_very_long_line(self):
        """超长单行返回合理的 token 数"""
        text = "x" * 50_000
        tokens = _estimate_tokens(text)
        # 50K 'x' chars: repeated chars compress heavily (~8 chars/token)
        assert 3_000 < tokens < 20_000, f"Expected 3K–20K tokens, got {tokens}"

    def test_unicode_emoji(self):
        """Emoji 和特殊 unicode 返回合理的 token 数"""
        text = "🔥 🚀 🎉 ✅ ❌ 你好世界 αβγδ"
        tokens = _estimate_tokens(text)
        assert 5 < tokens < 50, f"Expected 5–50 tokens, got {tokens}"

    def test_markdown_content(self):
        """Markdown 内容返回合理的 token 数"""
        text = """# Title

This is a **markdown** document with:
- List item 1
- List item 2

## Section 2

Some `inline code` and a [link](https://example.com).

```python
print("hello")
```
"""
        tokens = _estimate_tokens(text)
        assert 10 < tokens < 100, f"Expected 10–100 tokens, got {tokens}"


class TestDetectProjectType:
    """_detect_project_type() mock 文件检测测试"""

    def test_go_mod(self, tmp_path):
        """go.mod → 'go'"""
        (tmp_path / "go.mod").write_text("module example\n")
        assert _detect_project_type(tmp_path) == "go"

    def test_cargo_toml(self, tmp_path):
        """Cargo.toml → 'rust'"""
        (tmp_path / "Cargo.toml").write_text("[package]\n")
        assert _detect_project_type(tmp_path) == "rust"

    def test_pom_xml(self, tmp_path):
        """pom.xml → 'java'"""
        (tmp_path / "pom.xml").write_text("<project>\n</project>\n")
        assert _detect_project_type(tmp_path) == "java"

    def test_package_json(self, tmp_path):
        """package.json → 'node'"""
        (tmp_path / "package.json").write_text('{"name": "test"}\n')
        assert _detect_project_type(tmp_path) == "node"

    def test_pyproject_toml(self, tmp_path):
        """pyproject.toml → 'python'"""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        assert _detect_project_type(tmp_path) == "python"

    def test_setup_py(self, tmp_path):
        """setup.py → 'python'"""
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        assert _detect_project_type(tmp_path) == "python"

    def test_empty_directory_returns_unknown(self, tmp_path):
        """空目录 → 'unknown'"""
        assert _detect_project_type(tmp_path) == "unknown"

    def test_no_marker_files_returns_unknown(self, tmp_path):
        """只有无关文件 → 'unknown'"""
        (tmp_path / "README.md").write_text("# Project\n")
        (tmp_path / "src").mkdir()
        assert _detect_project_type(tmp_path) == "unknown"


class TestFindNextTicket:
    """_find_next_ticket() mock ticket 解析测试"""

    def _create_ticket(self, tickets_dir: Path, tid: str, name: str, extra: str = "") -> None:
        """Create a ticket file in the tickets directory."""
        content = f"# {name}\n\n{extra}"
        (tickets_dir / f"{tid}-{name}.md").write_text(content)

    def test_returns_first_uncompleted(self, tmp_path):
        """返回第一个未完成的 ticket"""
        tickets_dir = tmp_path / "scratch" / "tickets"
        tickets_dir.mkdir(parents=True)
        self._create_ticket(tickets_dir, "0001", "first")
        self._create_ticket(tickets_dir, "0002", "second")
        result = _find_next_ticket(tmp_path, set())
        assert result is not None
        tid, path = result
        assert tid == "0001"
        assert "0001-first.md" in path.name

    def test_skips_completed(self, tmp_path):
        """跳过已完成的 ticket"""
        tickets_dir = tmp_path / "scratch" / "tickets"
        tickets_dir.mkdir(parents=True)
        self._create_ticket(tickets_dir, "0001", "done-task")
        self._create_ticket(tickets_dir, "0002", "pending-task")
        completed = {"0001:done-task"}
        result = _find_next_ticket(tmp_path, completed)
        assert result is not None
        tid, path = result
        assert tid == "0002"

    def test_skips_all_completed_returns_none(self, tmp_path):
        """全部完成 → None"""
        tickets_dir = tmp_path / "scratch" / "tickets"
        tickets_dir.mkdir(parents=True)
        self._create_ticket(tickets_dir, "0001", "task-a")
        self._create_ticket(tickets_dir, "0002", "task-b")
        completed = {"0001:task-a", "0002:task-b"}
        assert _find_next_ticket(tmp_path, completed) is None

    def test_skips_archived(self, tmp_path):
        """跳过 status: archived 的 ticket"""
        tickets_dir = tmp_path / "scratch" / "tickets"
        tickets_dir.mkdir(parents=True)
        self._create_ticket(tickets_dir, "0001", "archived-task", extra="status: archived")
        self._create_ticket(tickets_dir, "0002", "active-task")
        completed: set[str] = set()
        result = _find_next_ticket(tmp_path, completed)
        assert result is not None
        tid, path = result
        assert tid == "0002"
        # _find_next_ticket 会修改 completed set 以缓存已扫描的 archived/skipped 条目
        assert "0001:archived-task" in completed

    def test_skips_skipped(self, tmp_path):
        """跳过 status: skipped 的 ticket"""
        tickets_dir = tmp_path / "scratch" / "tickets"
        tickets_dir.mkdir(parents=True)
        self._create_ticket(tickets_dir, "0001", "skipped-task", extra="status: skipped")
        self._create_ticket(tickets_dir, "0002", "active-task")
        completed: set[str] = set()
        result = _find_next_ticket(tmp_path, completed)
        assert result is not None
        tid, path = result
        assert tid == "0002"
        # _find_next_ticket 会修改 completed set 以缓存已扫描的 archived/skipped 条目
        assert "0001:skipped-task" in completed

    def test_empty_tickets_dir_returns_none(self, tmp_path):
        """tickets 目录不存在 → None"""
        assert _find_next_ticket(tmp_path, set()) is None


class TestCmdStatus:
    """cmd_status() 状态检查测试 — project_type 字段集成"""

    def _minimal_scratch(self, tmp_path: Path) -> None:
        """Create minimal scratch/ structure that makes has_scratch=True."""
        (tmp_path / "scratch").mkdir()
        (tmp_path / "scratch" / "SPEC.md").write_text("# spec\n")
        (tmp_path / "scratch" / "tickets").mkdir()

    def test_has_project_type_key(self, tmp_path):
        """state 始终包含 project_type 字段"""
        state = cmd_status(tmp_path)
        assert "project_type" in state

    def test_project_type_with_scratch_python(self, tmp_path):
        """有 scratch/ 时 project_type 反映项目类型 (python)"""
        self._minimal_scratch(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        state = cmd_status(tmp_path)
        assert state["project_type"] == "python"

    def test_project_type_with_scratch_node(self, tmp_path):
        """有 scratch/ 时 project_type 反映项目类型 (node)"""
        self._minimal_scratch(tmp_path)
        (tmp_path / "package.json").write_text('{"name": "test"}\n')
        state = cmd_status(tmp_path)
        assert state["project_type"] == "node"

    def test_project_type_with_scratch_go(self, tmp_path):
        """有 scratch/ 时 project_type 反映项目类型 (go)"""
        self._minimal_scratch(tmp_path)
        (tmp_path / "go.mod").write_text("module example\n")
        state = cmd_status(tmp_path)
        assert state["project_type"] == "go"

    def test_project_type_with_scratch_rust(self, tmp_path):
        """有 scratch/ 时 project_type 反映项目类型 (rust)"""
        self._minimal_scratch(tmp_path)
        (tmp_path / "Cargo.toml").write_text("[package]\n")
        state = cmd_status(tmp_path)
        assert state["project_type"] == "rust"

    def test_project_type_with_scratch_unknown(self, tmp_path):
        """有 scratch/ 但无标记文件时 project_type 为 unknown"""
        self._minimal_scratch(tmp_path)
        state = cmd_status(tmp_path)
        assert state["project_type"] == "unknown"

    def test_project_type_without_scratch(self, tmp_path):
        """没有 scratch/ 时 project_type 固定为 unknown（即使有标记文件）"""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        state = cmd_status(tmp_path)
        assert state["project_type"] == "unknown"

    def test_project_type_does_not_require_git(self, tmp_path):
        """无 git 仓库时 project_type 仍正常检测"""
        self._minimal_scratch(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        state = cmd_status(tmp_path)
        assert state["project_type"] == "python"
        assert state["has_git"] is False


class TestVerifyImplementation:
    """_verify_implementation() 验证流程测试"""

    @staticmethod
    def _setup_python_project(tmp_path: Path) -> None:
        """Create minimal python project structure for verification testing."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").write_text("")

    def test_unknown_project_type_returns_empty(self, tmp_path):
        """无项目类型时返回空列表（无验证步骤）"""
        errors = _verify_implementation(tmp_path)
        assert errors == []

    def test_python_project_runs_pytest(self, tmp_path):
        """Python 项目下运行 pytest 验证，测试通过返回空列表"""
        self._setup_python_project(tmp_path)
        (tmp_path / "tests" / "test_pass.py").write_text(
            "def test_pass():\n    assert True\n"
        )
        errors = _verify_implementation(tmp_path)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_python_project_pytest_failure(self, tmp_path):
        """Python 项目下 pytest 失败时返回 VerificationError"""
        self._setup_python_project(tmp_path)
        (tmp_path / "tests" / "test_fail.py").write_text(
            "def test_fail():\n    assert False\n"
        )
        errors = _verify_implementation(tmp_path)
        assert len(errors) > 0
        assert errors[0].step == "Python 测试"
        assert errors[0].exit_code != 0


class TestVerificationError:
    """VerificationError 格式化输出测试"""

    def test_str_contains_step_and_exit_code(self):
        """__str__() 包含步骤名和退出码"""
        err = VerificationError("Go vet", 1, "compilation error")
        s = str(err)
        assert "Go vet" in s
        assert "退出码 1" in s

    def test_str_contains_stderr_summary(self):
        """__str__() 包含 stderr 摘要"""
        err = VerificationError("Python 测试", 2, "FAILED test_foo.py::test_bar")
        s = str(err)
        assert "Python 测试" in s
        assert "FAILED test_foo.py::test_bar" in s
        assert "退出码 2" in s

    def test_multi_line_summary(self):
        """多行 stderr 仍包含在 __str__() 中"""
        err = VerificationError("Go vet", 127, "line1\nline2\nline3")
        s = str(err)
        assert "Go vet" in s
        assert "127" in s
        assert "line1" in s

    def test_zero_exit_code(self):
        """退出码为 0 时正确显示"""
        err = VerificationError("lint", 0, "no issues")
        s = str(err)
        assert "lint" in s
        assert "退出码 0" in s
