# 0003 — 多语言项目检测

**What to build:** auto-develop.py 自动检测 Go / Rust / Java 项目并运行对应的验证命令。

**Blocked by:** 0002（结构化错误报告框架）

**Status:** ready-for-agent

- [ ] 新增 `_detect_project_type(project: Path) -> str` 函数，按优先级检测：
  - `go.mod` → `"go"`
  - `Cargo.toml` → `"rust"`
  - `pom.xml` → `"java"`
  - `package.json` → `"node"`
  - `pyproject.toml` / `setup.py` → `"python"`
- [ ] 在 `_verify_implementation()` 中根据项目类型运行对应验证命令：
  - Go: `go vet ./...` + `go test ./...`
  - Rust: `cargo check` + `cargo test`
  - Java: `mvn test`
- [ ] 项目类型显示在 `--status` 输出中
- [ ] 工具链缺失（如没有 `go` / `cargo` / `mvn`）时优雅跳过，不 crash
- [ ] 集成到 Ticket 0002 的新错误框架中，返回 `VerificationError` 列表
