# ADR-0004：通用多工具部署 + Agent 代装

- 日期：2026-10-05
- 状态：已采纳
- 关联：[ADR-0001](0001-single-source-sync-deploy.md)

## 背景

v1 部署面绑定 ZCode × Cursor（`sync.sh` 硬编码两套路径），README 标题与文档同步特化。仓库公开后，用户使用的 Agent 工具各异（Claude Code / Codex / Gemini CLI / opencode…）。同期社区主流 skill / MCP 的分发惯例是：**只提供一句提示词给 Agent，Agent 自行完成安装**。

## 决策

1. **内容层只用通用约定**：`AGENTS.md` 规则、Markdown 命令、`SKILL.md` 技能、Markdown 子代理，不引入任何工具私有格式；工具特有格式（Cursor `.mdc` frontmatter）属于适配层，由脚本部署时生成，不进内容层。
2. **工具差异收敛为单张映射表**：`sync.sh` 的 `TOOL_TABLE`（名称 / 检测目录 / 规则路径与形态 / commands / skills / agents 目录，`-` 表示无此概念）。默认只部署本机检测到已安装的工具；`--target` 指定、`--all` 强制、`--list` 查看。适配新工具 = 加一行映射，不改代码。
3. **安装双通道**：
   - 人：`git clone` + `bash sync.sh --dry` + `bash sync.sh`；
   - Agent：README 提供一句话安装指令（clone → 读 README 与 sync.sh → dry-run → 部署 → 报告验证方式），任何 Agent 工具粘贴即装。
4. **映射表之外的工具**：内容既是通用 Markdown，让 Agent 照 README 的部署映射表手工部署即可；回馈则提 PR 加一行。
5. 覆盖前自动备份、内容有变化才覆盖、字节一致跳过等 v1 语义全部保留。

## 后果

- 任何支持上述通用约定（或近似约定）的工具开箱即用，无需等待官方适配。
- 各工具能力差异显式声明而非隐藏：Gemini CLI 仅部署全局规则（其命令为 TOML 格式）、Codex 命令进 `prompts/` 且无全局 skills/subagents 目录。
- 全局规则文件（`AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / `agent-os.mdc`）以仓库为单一事实源，目标处旧版被覆盖前进入备份目录。
- 代价：映射表中的目录约定需随各家工具演进维护（以官方文档为准）。
