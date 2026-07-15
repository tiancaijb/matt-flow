# 0003 — GitHub Release 自动化

**What to build:** GitHub Actions 在 push tag 时自动创建 Release。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 在 `.github/workflows/ci.yml` 中添加 release job：
  - 触发条件：push tags（`v*`）
  - 使用 `softprops/action-gh-release` 创建 Release
  - 自动生成 changelog（从 git log 取 tag 间的提交）
- [ ] YAML 语法验证通过
