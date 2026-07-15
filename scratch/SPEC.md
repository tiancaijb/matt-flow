# auto-develop.py 功能完善 — 规格说明书

## Problem Statement

当前 `scripts/auto-develop.py` 虽然能跑通基本流程，但在三个关键方面有不足：

1. **无工作量估算** — 无法判断一个 ticket 是否超出单个 context window（~100K tokens），导致 AI 在超大 ticket 上表现下降
2. **项目类型覆盖窄** — 只支持 npm（package.json）和 Python（pyproject.toml），Go/Rust/Java 等项目无法自动验证
3. **错误报告简陋** — 失败时只打印 "验证失败" 或笼统消息，用户不知道具体哪里出错

## Solution

增强 auto-develop.py，给它加三个能力：智能 ticket 估算、多语言项目检测、结构化错误报告。

## User Stories

1. 作为开发者，我希望 auto-develop.py 能估算 ticket 内容的 token 数，并在超出 ~100K 时警告，以便我在 Grill 阶段就合理拆分 ticket
2. 作为开发者，我希望 auto-develop.py 能自动检测 Go 项目（go.mod），运行 go vet 和 go test，以便 Go 项目也能用自动开发流程
3. 作为开发者，我希望 auto-develop.py 能自动检测 Rust 项目（Cargo.toml），运行 cargo check 和 cargo test，以便 Rust 项目也能用自动开发流程
4. 作为开发者，我希望 auto-develop.py 能自动检测 Java/Maven 项目（pom.xml），运行 mvn test，以便 Java 项目也能用自动开发流程
5. 作为开发者，我希望 auto-develop.py 在验证失败时输出结构化的错误报告（哪个步骤失败、退出码、stderr 摘要），以便我能快速定位问题
6. 作为开发者，我希望 auto-develop.py 在 --status 输出中加入项目类型检测结果和错误历史，以便了解项目的整体健康度

## Implementation Decisions

### A: Token 估算

- 使用 `tiktoken` Python 库（OpenAI 的 tokenizer）估算 ticket 内容 + spec 上下文的 token 数
- 如果 tiktoken 不可用，回退到简单估算（len(text) / 3.5 ≈ tokens）
- 阈值：> 100K tokens 发警告，> 140K tokens 标记为"超出智能区"
- 在 `--status` 输出中显示每个 ticket 的 token 估算值，标记过大需拆分的 ticket
- 估算只在 `--status` 和 `--run` 的预处理阶段执行，不影响 implement 流程

### B: 多语言检测

- 在 `_verify_implementation()` 中按优先级检测项目类型并运行对应验证命令
- 检测顺序（按特征文件存在性）：
  1. `go.mod` → `go vet ./...` + `go test ./...`
  2. `Cargo.toml` → `cargo check` + `cargo test`
  3. `pom.xml` → `mvn test`（需 mvn 在 PATH 中）
  4. `package.json` → `npx tsc --noEmit` + `npm run build` + `npm test`（已有）
  5. `pyproject.toml` / `setup.py` → `python3 -m pytest -x -q`（已有）
- 每种语言检测是独立的，项目可能同时匹配多种（如 monorepo）

### C: 结构化错误报告

- 定义 `VerificationError` 异常类，包含：step（步骤名）、exit_code、stdout_summary、stderr_summary
- `_verify_implementation()` 改为返回 `list[VerificationError]` 而非 bool
- `cmd_run()` 中捕获并格式化输出，每个失败步骤一行：
  ```
  ❌ 验证失败 (ticket-0003):
     • TypeScript 类型检查 → 退出码 2
       src/cli.ts:42: error TS2322: Type 'string' is not assignable to type 'number'
     • 测试套件 → 退出码 1
       FAIL tests/cli.test.ts (2 failed)
  ```
- `--status` 输出新增 `last_error` 字段（从 git 历史或临时文件读取）

## Testing Decisions

- Token 估算函数需要单元测试（边界值：0 token、100K、140K、200K）
- 多语言检测测试通过 mock 项目文件（创建临时目录放 go.mod / Cargo.toml 等）
- 错误报告测试通过注入模拟的 VerificationError
- 测试优先：先写测试再实现（Matt 的 TDD 风格）

## Out of Scope

- 安装 tiktoken 不在 auto-develop.py 的责任范围，由用户自行 pip install
- 不在本批次添加 CI/CD 集成
- 不修改 `init-project.py`

## Further Notes

- auto-develop.py 是 skill 目录中的通用模板，需要保持向后兼容
- 所有新增功能在缺少依赖（如 tiktoken、mvn）时应优雅回退，不能 crash
