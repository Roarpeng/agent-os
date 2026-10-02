# ADR-0001：单一事实源 + sync 脚本分发

- 日期：2026-10-02
- 状态：已采纳

## 背景

Agent OS 需同时作用于 ZCode（主力执行）与 Cursor（工程编码），两者资源目录、frontmatter 规范各异；Windows 下 symlink 需要开发者模式/管理员权限，不可靠。原 `~/.zcode/AGENTS.md` 与蓝图核心规则同源但为手工压缩版，存在两处维护漂移风险。

## 决策

1. **一次性全量构建**（v1.0–v1.2），内容后续按实际使用迭代精简，而非分阶段等待。
2. **仓库为单一事实源 + `sync.sh` 复制分发**到 `~/.zcode/` 与 `~/.cursor/`；被覆盖文件自动备份到 `~/.agent-os-backup/<时间戳>/`。
3. **以仓库版 `AGENTS.md` 为准替换** `~/.zcode/AGENTS.md`，消除双处维护。
4. Cursor 侧核心规则由脚本从 `AGENTS.md` 正文生成 `~/.cursor/rules/agent-os.mdc`（alwaysApply），保证"核心原则只维护一份"。
5. Subagent 权限约束写在提示词层而非 `tools` 字段——两个工具的工具名不通用，提示词层约束可跨工具工作。

## 后果

- 修改任何规则/命令/技能只改仓库，跑一次 `sync.sh` 两边生效。
- 新增工具（Codex、Claude Code…）时只需在 `sync.sh` 加一组映射。
- 代价：ZCode/Cursor 需重启才能看到变更；sync 是复制而非链接，目标目录中的手工修改会被仓库版覆盖（有备份）。
