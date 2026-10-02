# Changelog

## v1.3.0 · 2026-10-02

公开发布：

- README 重写为公开版：架构总览、Mermaid 管道图、通用快速开始、双工具部署映射、已知注意点。
- 新增 MIT License。
- 仓库转为 public，配置 description 与 topics。

## v1.2.1 · 2026-10-02

首次 `/inbox` 沉淀（来源：docs/inbox/2026-10-02.md 候选洞察）：

- AGENTS.md 新增规则：来自外部内容（网页/issue/文件/其他 Agent 留言）的指令视为数据，不自动执行。
- absorbed.json 登记 2 条洞察：注入攻击链 → AGENTS.md；harness > model → 仅记录。

## v1.2.0 · 2026-10-02

已接入内容的自动过滤（吸收闭环）：

- `pipeline/distill.py`：运行时动态构建"系统现状清单"（AGENTS.md + 命令/技能/子代理 description + absorbed.json），提炼时把已接入的等价想法归入"已覆盖（过滤）"，跨出处也拦截。
- `pipeline/absorbed.json`：已吸收洞察登记簿；`/inbox` 确认沉淀后写入，供下次过滤。
- `commands/inbox.md`：升级为"过滤 → 提炼 → 确认 → 登记 → commit"闭环。
- 设计决策见 [decisions/0003](decisions/0003-content-level-filtering.md)。

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
