# Changelog

## v1.1.0 · 2026-10-02

自动灵感管道（让大佬的思想自动流进仓库，自动采集 + 人工沉淀）：

- `pipeline/sources.json`：来源配置（rss / hn / github 三类，可自由增删）。
- `pipeline/fetch_digest.py`：纯标准库抓取器，去重后写 `docs/inbox/<日期>.md`。
- `pipeline/distill.py`：可选 LLM 提炼（OpenAI 兼容接口，未配密钥自动跳过）。
- `.github/workflows/digest.yml`：每日 09:30（北京时间）定时 + 手动触发。
- `commands/inbox.md`：`/inbox` 命令——提炼候选经验，人工确认后才沉淀。
- 设计决策：管道永不直接修改规则文件，见 [decisions/0002](decisions/0002-auto-thought-intake.md)。

## v1.0.0 · 2026-10-02

初始构建（一次性完成 v1.0–v1.2 路线）：

- `AGENTS.md`：10 行核心规则，唯一常驻全局上下文。
- Commands ×6：`plan` `research` `debug` `review` `verify` `html`。
- Skills ×4：`deep-research` `architecture` `industrial-ai` `html-artifact`。
- Subagents ×3：`researcher`（只读研究）`reviewer`（只读审查）`architect`（只设计不改码）。
- `sync.sh`：仓库 → `~/.zcode/` 与 `~/.cursor/` 分发，覆盖前自动备份。
- docs：design.md、changelog.md、decisions/0001。

决策背景见 [decisions/0001-single-source-sync-deploy.md](decisions/0001-single-source-sync-deploy.md)。
