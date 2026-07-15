# 0002 — install.sh 润色

**What to build:** 改进 install.sh 的交互体验：curl 失败回退提示、已安装组件检测提示。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] curl 下载 SKILL.md 或 scripts 失败时，输出更友好的错误提示（含手动安装命令）
- [ ] 检测到 Node.js 或 pi 或 Matt Skills 已安装时，明确显示 "✓ 已安装" 而不是 "跳过"
- [ ] 运行 `bash -n install.sh` 验证语法
