"""
Tests for scripts/auto-develop.py — _estimate_tokens()
======================================================

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
