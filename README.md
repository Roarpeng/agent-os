# Agent OS · ZCode × Cursor

个人 Agent 工作系统：**低 Token、可维护、可迁移**。
本仓库是唯一事实源；`sync.sh` 分发到 ZCode 与 Cursor，两边共用同一套方法论。

```
Understand → Choose Mode → Plan → Execute → Verify → Deliver
```

## 结构

```
AgentOs/
├── AGENTS.md        # 核心规则（唯一常驻全局上下文，~10 行）
├── commands/        # 6 个高频动作：plan research debug review verify html
├── skills/          # 4 个专业方法论：deep-research architecture industrial-ai html-artifact
├── agents/          # 3 个子代理：researcher reviewer architect
├── docs/            # 设计文档、变更记录、决策记录（ADR）、原始蓝图 blueprint.html
└── sync.sh          # 部署脚本（Git Bash）
```

## 快速开始

```bash
# 修改仓库内容后同步（Git Bash）
bash sync.sh --dry   # 预览
bash sync.sh         # 部署
```

同步后**重启 ZCode / Cursor** 生效。

## 部署映射

| 仓库 | ZCode | Cursor |
|---|---|---|
| `AGENTS.md` | `~/.zcode/AGENTS.md`（全局指令） | `~/.cursor/rules/agent-os.mdc`（脚本自动加 alwaysApply frontmatter） |
| `commands/*.md` | `~/.zcode/commands/` → `/plan` 等 | `~/.cursor/commands/` |
| `skills/*/` | `~/.zcode/skills/` | `~/.cursor/skills/` |
| `agents/*.md` | `~/.zcode/agents/` | `~/.cursor/agents/` |

- 被覆盖的旧文件自动备份到 `~/.agent-os-backup/<时间戳>/`。
- 与已有资源不冲突：graphflow、typesafe-ai 等 skill 保持原样。

## 验证清单（部署后）

- ZCode：输入 `/` → Commands 组能看到 6 个命令；Settings → Skills 出现 4 个新 skill；Settings → Subagents 出现 3 个角色。
- Cursor：输入 `/` 能看到命令；对话中 `@researcher` 等可引用。

已知注意点：
1. ZCode 中命令名若与内置命令重名，会被从 `/` 菜单过滤（文件仍在）。如遇某个命令不出现，重命名 `commands/` 下对应文件后重新 sync。
2. 若 ZCode 版本不识别 `~/.zcode/agents/`（Settings → Subagents 为空），可在设置界面手动导入 `agents/*.md`；Cursor 侧 `~/.cursor/agents/` 为官方支持路径。
3. 若 Cursor 版本不支持全局 `~/.cursor/commands/`，把 `commands/*.md` 复制到项目的 `.cursor/commands/`。

## 自动灵感管道（GitHub Actions）

让大佬的思想自动流进仓库：每天北京时间 09:30 自动抓取 `pipeline/sources.json` 声明的来源（Karpathy / Simon Willison / Lilian Weng / Armin Ronacher 的博客，HN 提及 Karpathy，karpathy 的 GitHub 动态），去重后写入 `docs/inbox/<日期>.md`。

```bash
gh workflow run digest     # 手动触发一次（首次部署后建议跑一次验证）
/inbox                      # 在 ZCode 中提炼候选经验；人工确认后才沉淀
```

- **来源配置**：编辑 `pipeline/sources.json`——`rss`（博客）/ `hn`（Hacker News 关键词）/ `github`（用户动态）三类，增删自由。
- **LLM 提炼（可选）**：仓库 Settings → Secrets and variables → Actions 添加 `LLM_API_KEY`（OpenAI 兼容接口）。用智谱 GLM 则同时设置 `LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4`、`LLM_MODEL=glm-4-flash`（免费）。不配置则只有原始 digest，`/inbox` 仍可工作。
- **沉淀门槛**：自动管道只采集和提炼，**永不直接修改** AGENTS.md / commands / skills；沉淀必须经 `/inbox` 提炼 + 人工确认（见 ADR-0002）。

## 设计与迭代

- 设计文档：[docs/design.md](docs/design.md)；原始蓝图：[docs/blueprint.html](docs/blueprint.html)
- 决策记录：[docs/decisions/](docs/decisions/)
- 迭代原则：**只把反复出现且长期有效的经验升级为 Rule/Skill**，避免 Memory 和 Rules 无限膨胀；每次变更记入 [docs/changelog.md](docs/changelog.md)。

## Definition of Done（Agent 结束任务前的最小检查）

- [ ] 真正理解了用户目标？
- [ ] 选择了合适的输出媒介？
- [ ] 避免了无关修改？
- [ ] 完成了必要验证？
- [ ] 保留了关键约束？
- [ ] 产生了可执行结果？
