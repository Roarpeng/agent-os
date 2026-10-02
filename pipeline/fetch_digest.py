#!/usr/bin/env python3
"""Agent OS · 灵感抓取器

从 pipeline/sources.json 声明的来源抓取最新动态（RSS / HN / GitHub），
按 state.json 去重后写入 docs/inbox/<日期>.md。
纯标准库、零依赖、零密钥；本地与 GitHub Actions 均可运行。
"""
import html as html_mod
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "docs" / "inbox"
STATE_FILE = ROOT / "pipeline" / "state.json"
SOURCES_FILE = ROOT / "pipeline" / "sources.json"

MAX_PER_SOURCE = 10   # 每来源每次最多收录条数
SEEN_CAP = 500        # 每来源最多记忆的已见 ID 数
UA = "agent-os-digest/1.0 (personal pipeline)"


def http_get(url: str, token: str | None = None, as_json: bool = False):
    headers = {"User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw) if as_json else raw


def strip_html(text: str, limit: int = 280) -> str:
    text = text or ""
    # 先丢弃 style/script 整块内容，再剥其余标签——否则摘要里会混入 CSS/JS 文本
    text = re.sub(r"(?is)<(style|script)[^>]*>.*?</\1\s*>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(xml_text: str) -> list[dict]:
    """容错解析 RSS 2.0 / Atom（忽略命名空间）。"""
    root = ET.fromstring(xml_text)
    items = []
    for el in root.iter():
        if localname(el.tag) not in ("item", "entry"):
            continue
        d: dict = {}
        for child in el.iter():
            name = localname(child.tag)
            text = (child.text or "").strip()
            if name == "link":
                d.setdefault("link", child.get("href") or text)
            elif name == "title":
                d.setdefault("title", strip_html(text, 200))
            elif name in ("pubDate", "published", "updated"):
                d.setdefault("date", text)
            elif name in ("summary", "description"):
                d.setdefault("summary", strip_html(text))
        items.append(d)
    return items


def fetch_rss(src: dict) -> list[dict]:
    out = []
    for it in parse_feed(http_get(src["url"]))[:30]:
        title = it.get("title") or "(无标题)"
        out.append({
            "id": it.get("link") or title,
            "title": title,
            "link": it.get("link", ""),
            "meta": it.get("date", ""),
            "snippet": it.get("summary", ""),
        })
    return out


def fetch_hn(src: dict) -> list[dict]:
    q = urllib.parse.quote(src["query"])
    url = (f"https://hn.algolia.com/api/v1/search_by_date?query={q}"
           f"&tags=story&hitsPerPage=30")
    out = []
    for h in http_get(url, as_json=True).get("hits", []):
        oid = str(h.get("objectID", ""))
        link = h.get("url") or f"https://news.ycombinator.com/item?id={oid}"
        out.append({
            "id": f"hn-{oid}",
            "title": h.get("title") or "(无标题)",
            "link": link,
            "meta": (f"{h.get('points', 0)} 分 · {h.get('num_comments', 0)} 评论"
                     f" · {(h.get('created_at') or '')[:10]}"),
            "snippet": strip_html(h.get("story_text") or "", 200),
        })
    return out


KEEP_EVENTS = ("ReleaseEvent", "PublicEvent", "CreateEvent", "ForkEvent")


def fetch_github(src: dict) -> list[dict]:
    token = os.environ.get("GITHUB_TOKEN") or None
    events = http_get(f"https://api.github.com/users/{src['user']}/events/public",
                      token=token, as_json=True)
    out = []
    for e in events:
        if e.get("type") not in KEEP_EVENTS:
            continue
        repo = (e.get("repo") or {}).get("name", "")
        detail = ""
        if e.get("type") == "ReleaseEvent":
            rel = (e.get("payload") or {}).get("release") or {}
            detail = rel.get("tag_name", "")
        label = f"{e.get('type')} · {repo}" + (f" · {detail}" if detail else "")
        out.append({
            "id": f"gh-{e.get('id', '')}",
            "title": label,
            "link": f"https://github.com/{repo}",
            "meta": (e.get("created_at") or "")[:10],
            "snippet": "",
        })
    return out


FETCHERS = {"rss": fetch_rss, "hn": fetch_hn, "github": fetch_github}


def main() -> int:
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))["sources"]
    state = (json.loads(STATE_FILE.read_text(encoding="utf-8"))
             if STATE_FILE.exists() else {"seen": {}})
    seen: dict = state.setdefault("seen", {})

    sections: list[tuple[str, list[dict]]] = []
    total_new = 0

    for src in sources:
        key = (f"{src['type']}:" +
               (src.get("url") or src.get("query") or src.get("user") or src.get("name", "?")))
        fetcher = FETCHERS.get(src["type"])
        if not fetcher:
            print(f"!! 未知来源类型 {src['type']}，跳过: {src.get('name')}")
            continue
        try:
            entries = fetcher(src)
        except Exception as exc:
            print(f"!! 抓取失败，跳过 {src.get('name')}: {exc}")
            continue

        known_list: list = seen.get(key, [])
        known = set(known_list)
        fetched = [e for e in entries if e["id"]]
        # 只发布最新的 N 条；整个抓取窗口都记为已见（基线语义），
        # 否则旧库存会按每次 10 条被反复翻出，同一批内容重复进 digest。
        fresh = [e for e in fetched if e["id"] not in known][:MAX_PER_SOURCE]
        if fetched:
            merged = list(dict.fromkeys(known_list + [e["id"] for e in fetched]))
            seen[key] = merged[-SEEN_CAP:]
        if fresh:
            sections.append((src.get("name", key), fresh))
            total_new += len(fresh)

    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    if not total_new:
        print("无新内容，未生成 digest。")
        return 0

    INBOX.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path = INBOX / f"{today}.md"
    parts = []
    if path.exists():
        parts.append(f"\n## 补充 · {datetime.now().strftime('%H:%M')}\n")
    else:
        parts.append(f"# 灵感 Digest · {today}\n\n"
                     "> 自动抓取自 `pipeline/sources.json`。用 `/inbox` 让 Agent 提炼候选经验；"
                     "人工确认后才沉淀为规则/技能。\n")
    for name, entries in sections:
        lines = [f"\n## {name}\n"]
        for e in entries:
            safe_title = e["title"].replace("[", "(").replace("]", ")")
            head = f"- [{safe_title}]({e['link']})"
            if e["meta"]:
                head += f" — {e['meta']}"
            lines.append(head)
            if e["snippet"]:
                lines.append(f"  > {e['snippet']}")
        parts.append("\n".join(lines) + "\n")

    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(parts))

    print(f"新条目 {total_new} 条 → {path}")
    for name, entries in sections:
        print(f"  {name}: {len(entries)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
