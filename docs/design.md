# Agent OS 设计

> 单一事实源：本仓库。本文是设计要点；完整视觉版见 [blueprint.html](blueprint.html)。

## 1. 核心思想

不是让 Agent 写更多，而是让 Agent 选择更好的完成方式：

1. **Think**：先理解，再行动。先读上下文、确认目标和约束，不看到问题就猜。
2. **Medium**：先选输出媒介。Text → Table → Diagram/SVG → HTML，复杂关系优先可视化。
3. **Verify**：执行后验证。不把"看起来正确"当成完成。

## 2. 分层架构：上下文的按需加载

| 层 | 载体 | 加载时机 | 职责 | Token 成本 |
|---|---|---|---|---|
| AGENTS.md | ~10 行全局规则 | 每次会话常驻 | 工作原则 | 恒定，极低 |
| Commands | 6 个短指令 | 用户显式 `/xxx` 触发 | 高频动作流程模板 | 按需，一次性 |
| Skills | 4 个方法论 | 按任务匹配加载 | 专业流程 | 按需 |
| Subagents | 3 个角色 | 主 Agent 调度 | 隔离上下文 + 职责边界 | 隔离（不占主上下文） |
| Artifact | 交付物 | — | 最终产出 | — |

设计约束：**复杂内容一律下沉，不进 AGENTS.md**；AGENTS.md 是唯一建议长期常驻的全局规则。

## 3. 资源清单

**Commands**（文件名即命令，`$ARGUMENTS` 接参）：

| 命令 | 用途 | 关联 |
|---|---|---|
| `/plan` | 最小计划：目标→步骤→风险→验证 | — |
| `/research` | 深度研究：一手资料、交叉验证 | 自动挂载 deep-research skill；可委派 researcher |
| `/debug` | 根因调试：读取→复现→根因→最小修改→验证 | — |
| `/review` | 代码审查：P0/P1/P2 分级 | 可委派 reviewer |
| `/verify` | 结果验证：实际执行并输出依据 | — |
| `/html` | HTML Artifact：先判断价值再构建 | 自动挂载 html-artifact skill |

**Skills**：deep-research（研究方法论）、architecture（架构设计）、industrial-ai（工业 AI：AI 做理解/规划，确定性系统负责实时执行）、html-artifact（单文件构建规范）。

**Subagents**：

| 角色 | 职责 | 权限（提示词层约束） |
|---|---|---|
| researcher | 搜索、交叉验证、发现 Gap | 只读 |
| reviewer | 找 Bug、遗漏、风险、回归 | 只读（可运行只读命令取证） |
| architect | 需求、约束、架构、实施方案 | 只设计，不改代码 |

> 权限约束写在提示词层而非 tools 字段：ZCode 与 Cursor 的工具名不通用，提示词层约束可跨工具工作。

## 4. 双工具策略

- **ZCode**：Agent OS 主力执行。全局指令 `~/.zcode/AGENTS.md`。
- **Cursor**：工程编码与协作。核心规则经 sync 脚本转为 `~/.cursor/rules/agent-os.mdc`（alwaysApply）。
- **维护原则**：核心方法论只维护一份（本仓库）；工具特有配置才单独适配。换 Codex、Claude Code 等其他 Agent 时，只需扩展 sync 脚本的映射，不重写系统。

## 5. 落地路线

| 版本 | 内容 | 状态 |
|---|---|---|
| v1.0 | 短版 AGENTS.md + 6 Commands | ✅ 2026-10-02 |
| v1.1 | 4 Skills | ✅ 2026-10-02（一次性全量构建） |
| v1.2 | 3 Subagents | ✅ 2026-10-02 |
| v2.0 | 自动路由：按任务复杂度自动选 Command/Skill/Subagent/模型 | 待实践沉淀 |
| v2.x | 经验沉淀：反复出现且长期有效的经验才升级为 Rule | 持续 |

## 6. Definition of Done

理解目标 / 选对媒介 / 无关修改为零 / 必要验证完成 / 关键约束保留 / 结果可执行。
