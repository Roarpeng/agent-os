# ADR-0002：自动灵感管道——自动采集，人工沉淀

- 日期：2026-10-02
- 状态：已采纳

## 背景

Agent OS 的 v2.x 目标是"经验沉淀"，但经验来源依赖手工偶遇。Agent OS 思路本身来自 Karpathy 的分享——这类高密度来源（个人博客、HN 讨论、GitHub 动态）完全可以自动采集。

## 决策

1. **GitHub Actions 每日定时**（北京时间 09:30）运行 `pipeline/fetch_digest.py`：RSS + HN Algolia API + GitHub Events API。纯标准库、零第三方依赖、零必需密钥，机器关机也能跑。
2. **去重状态** `pipeline/state.json` 随仓库提交；产出为 `docs/inbox/<日期>.md` 原始 digest。
3. **LLM 提炼为可选增强**（`pipeline/distill.py`，OpenAI 兼容密钥），只向 digest 追加"候选洞察"段落；失败不阻断流程。
4. **管道永不直接修改 AGENTS.md / commands / skills**。沉淀必须经 `/inbox` 命令提炼 + 人工确认。
5. 来源集中声明在 `pipeline/sources.json`，换人/加人只改配置不改代码。

### 为什么不允许自动改规则

与仓库哲学一致："只把反复出现且长期有效的经验升级为 Rule，避免 Rules 无限膨胀"。自动写入会以每天数条的速度稀释规则库；门槛（人工确认）正是过滤器。新增一条规则的持续成本是之后每次会话都为它付 Token——这个成本必须由人拍板。

## 后果

+ 每天早上有一份现成的大佬动态摘要；`/inbox` 一步进入提炼流程。
+ 私库 Actions 免费额度 2000 分钟/月，本管道约 60 分钟/月，余量充足。
- 需要仓库托管在 GitHub；LLM 提炼需自备密钥（不配置则只有原始 digest，`/inbox` 仍可用）。
- HN/GitHub API 未认证限额对本场景（每日一次）足够，但来源大幅增加时需注意。
