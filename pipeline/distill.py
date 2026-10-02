#!/usr/bin/env python3
"""Agent OS · 灵感提炼器（可选）

配置了 LLM_API_KEY（OpenAI 兼容接口）时，对最新 digest 做提炼，
把"候选洞察"追加到该 digest；未配置则自动跳过，不阻断工作流。
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "docs" / "inbox"

SYSTEM_PROMPT = """你是 Agent OS（个人 Agent 工作系统）的灵感提炼器。
输入是自动抓取的技术研究者/工程师的公开动态 digest。

任务：提炼最多 5 条对"个人 Agent 工作系统"真正有价值的洞察。要求：
- 宁缺毋滥：与 Agent OS 现有原则（先理解再行动、最小修改、执行后验证、上下文按需加载）重复的不要输出；营销、八卦、与 Agent 工作流无关的新闻不要输出。
- 每条格式：
  ### 洞察 N：<一句话洞察>
  - 依据：<来源链接>
  - 分类：<规则候选 | 命令/技能候选 | 方法论 | 不值得沉淀>
  - 建议：<一句话行动建议>
- 用中文，短句，直接可执行。
"""

MAX_INPUT_CHARS = 15000


def main() -> int:
    api_key = (os.environ.get("LLM_API_KEY") or "").strip()
    if not api_key:
        print("LLM_API_KEY 未配置，跳过提炼（digest 保留原始内容）。")
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

    payload = json.dumps({
        "model": model,
        "temperature": 0.3,
        "max_tokens": 1500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:MAX_INPUT_CHARS]},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = (data["choices"][0]["message"]["content"] or "").strip()
    if not content:
        print("模型返回空内容，跳过。")
        return 0

    with latest.open("a", encoding="utf-8") as f:
        f.write(f"\n\n## 候选洞察（LLM 提炼 · {model}）\n\n{content}\n")
    print(f"提炼完成 → {latest.name}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"!! 提炼失败（不影响已抓取的 digest）: {exc}")
        sys.exit(0)
