#!/usr/bin/env python3
"""Agent OS · 灵感提炼器（可选，建议配置）

对最新 digest 做提炼 + 内容级过滤：
  1. 运行时动态构建"系统现状清单"——AGENTS.md 全文、全部命令/技能/子代理的
     description、absorbed.json 里的历史已吸收洞察。
  2. LLM 对照清单做等价判断：与已接入内容等价的想法归入"已覆盖（过滤）"节，
     不再作为候选洞察输出（透明可审计，不静默丢弃）。
未配置 LLM_API_KEY 时自动跳过，不阻断工作流（此时过滤由本地 /inbox 用会话模型完成）。
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "docs" / "inbox"

MAX_DIGEST_CHARS = 15000
MAX_MANIFEST_CHARS = 4000

SYSTEM_PROMPT = """你是 Agent OS（个人 Agent 工作系统）的灵感提炼器。
输入包含两部分：【系统现状清单】是当前已接入的规则、命令、技能、子代理和历史已吸收洞察；【今日 digest】是自动抓取的技术研究者/工程师公开动态。

任务：从 digest 提炼最多 5 条对 Agent OS 真正有价值的新洞察。

过滤规则（最重要）：
- 与【系统现状清单】中任何一条等价或高度重叠的想法，视为"已接入"，不得作为洞察输出；把它们归入"已覆盖（过滤）"小节，各注明被哪条现有规则/技能/命令/历史洞察覆盖。
- 同一想法换了出处（新文章/访谈/转述）同样过滤——判断对象是想法，不是链接。
- 营销、八卦、与 Agent 工作流无关的新闻不要输出。

输出格式（中文、短句、宁缺毋滥——允许零洞察、全部过滤）：
## 洞察
### 洞察 N：<一句话洞察>
- 依据：<来源链接>
- 分类：<规则候选 | 命令/技能候选 | 方法论 | 不值得沉淀>
- 建议：<一句话行动建议>
## 已覆盖（过滤）
- <条目/主题> ← 已由 <现有规则/技能/命令/历史洞察> 覆盖
"""


def frontmatter_desc(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^description:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def build_manifest() -> str:
    """把 Agent OS 当前已接入的能力压缩成一份清单，作为过滤依据。
    每次运行时从文件动态生成：新增/修改规则、技能后，过滤自动跟上。"""
    parts = []

    agents_md = ROOT / "AGENTS.md"
    if agents_md.exists():
        parts.append("### 全局规则 AGENTS.md\n" +
                     agents_md.read_text(encoding="utf-8").strip())

    for label, folder, pattern, naming in (
        ("已有 Commands", ROOT / "commands", "*.md", lambda p: f"/{p.stem}"),
        ("已有 Skills", ROOT / "skills", "*/SKILL.md", lambda p: p.parent.name),
        ("已有 Subagents", ROOT / "agents", "*.md", lambda p: p.stem),
    ):
        descs = [f"- {naming(p)}: {d}" for p in sorted(folder.glob(pattern))
                 if (d := frontmatter_desc(p))]
        if descs:
            parts.append(f"### {label}\n" + "\n".join(descs))

    absorbed = ROOT / "pipeline" / "absorbed.json"
    if absorbed.exists():
        items = json.loads(absorbed.read_text(encoding="utf-8")).get("absorbed", [])
        if items:
            lines = [f"- [{it.get('date', '')}] {it.get('insight', '')}"
                     f" → 已沉淀到 {it.get('into', '')}"
                     for it in items[-30:]]
            parts.append("### 历史已吸收洞察（同样视为已接入，勿重复提出）\n"
                         + "\n".join(lines))

    return "\n\n".join(parts)[:MAX_MANIFEST_CHARS]


def chat(base: str, api_key: str, model: str, system: str, user: str) -> str:
    """按 base URL 自动适配协议：智谱同时提供 OpenAI 兼容(/api/paas/v4)
    和 Anthropic 兼容(/api/anthropic)两种端点，请求与响应结构不同。"""
    if "/api/anthropic" in base:
        url = f"{base}/v1/messages"
        headers = {"Content-Type": "application/json",
                   "x-api-key": api_key,
                   "anthropic-version": "2023-06-01"}
        payload = {"model": model, "max_tokens": 1500, "temperature": 0.3,
                   "system": system,
                   "messages": [{"role": "user", "content": user}]}
    else:  # OpenAI 兼容（含智谱 /api/paas/v4、OpenAI 官方等）
        url = f"{base}/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {api_key}"}
        payload = {"model": model, "temperature": 0.3, "max_tokens": 1500,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]}

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if "choices" in data:  # OpenAI 结构
        return (data["choices"][0]["message"]["content"] or "").strip()
    # Anthropic 结构：content 是块数组
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text").strip()


def main() -> int:
    api_key = (os.environ.get("LLM_API_KEY") or "").strip()
    if not api_key:
        print("LLM_API_KEY 未配置，跳过提炼与过滤（由本地 /inbox 承担）。")
        return 0
    base = (os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL") or "gpt-4o-mini"

    digests = sorted(INBOX.glob("*.md"))
    if not digests:
        print("没有可提炼的 digest。")
        return 0
    latest = digests[-1]
    text = latest.read_text(encoding="utf-8")
    if "候选洞察" in text:
        print(f"{latest.name} 已提炼过，跳过。")
        return 0

    manifest = build_manifest()
    user_content = (f"【系统现状清单】\n{manifest}\n\n"
                    f"【今日 digest】\n{text[:MAX_DIGEST_CHARS]}")

    content = chat(base, api_key, model, SYSTEM_PROMPT, user_content)
    if not content:
        print("模型返回空内容，跳过。")
        return 0

    with latest.open("a", encoding="utf-8") as f:
        f.write(f"\n\n## 候选洞察（LLM 提炼 · {model}）\n\n{content}\n")
    print(f"提炼+过滤完成 → {latest.name}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"!! 提炼失败（不影响已抓取的 digest）: {exc}")
        sys.exit(0)
