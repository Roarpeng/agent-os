#!/usr/bin/env bash
# Agent OS 同步脚本：本仓库（单一事实源）→ ZCode (~/.zcode) 与 Cursor (~/.cursor)
# 用法：bash sync.sh          全量同步
#       bash sync.sh --dry    只看会做什么，不写入
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCODE="${ZCODE_HOME:-$HOME/.zcode}"
CURSOR="${CURSOR_HOME:-$HOME/.cursor}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_ROOT="$HOME/.agent-os-backup"
DRY="${1:-}"

# deploy <src> <dst> —— 内容有变化才覆盖；覆盖前备份旧文件
deploy() {
  local src="$1" dst="$2"
  local rel="${dst#$HOME/}"
  if [ -n "$DRY" ] && [ "$DRY" = "--dry" ]; then
    if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
      echo "  = 一致: $rel"
    elif [ -f "$dst" ]; then
      echo "  + 更新: $rel"
    else
      echo "  + 新增: $rel"
    fi
    return
  fi
  mkdir -p "$(dirname "$dst")"
  if [ -f "$dst" ] && ! cmp -s "$src" "$dst"; then
    mkdir -p "$BACKUP_ROOT/$STAMP/$(dirname "$rel")"
    cp "$dst" "$BACKUP_ROOT/$STAMP/$rel"
    echo "  + 更新: $rel（旧文件已备份）"
  elif [ ! -f "$dst" ]; then
    echo "  + 新增: $rel"
  else
    echo "  = 一致: $rel"
  fi
  cp "$src" "$dst"
}

echo "== Agent OS sync =="
echo "-- ZCode ($ZCODE) --"
deploy "$ROOT/AGENTS.md" "$ZCODE/AGENTS.md"

for f in "$ROOT"/commands/*.md; do
  deploy "$f" "$ZCODE/commands/$(basename "$f")"
done

for d in "$ROOT"/skills/*/; do
  name="$(basename "$d")"
  deploy "$d/SKILL.md" "$ZCODE/skills/$name/SKILL.md"
done

for f in "$ROOT"/agents/*.md; do
  deploy "$f" "$ZCODE/agents/$(basename "$f")"
done

echo "-- Cursor ($CURSOR) --"
# 核心规则：AGENTS.md 正文 + Cursor .mdc frontmatter（始终生效）
MDC="$(mktemp)"
{
  printf -- '---\n'
  printf 'description: Agent OS 核心工作规则（理解→选择→执行→验证→交付）\n'
  printf 'alwaysApply: true\n'
  printf -- '---\n\n'
  tail -n +2 "$ROOT/AGENTS.md"   # 跳过标题行，保留规则正文
} > "$MDC"
deploy "$MDC" "$CURSOR/rules/agent-os.mdc"
rm -f "$MDC"

for f in "$ROOT"/commands/*.md; do
  deploy "$f" "$CURSOR/commands/$(basename "$f")"
done

for d in "$ROOT"/skills/*/; do
  name="$(basename "$d")"
  deploy "$d/SKILL.md" "$CURSOR/skills/$name/SKILL.md"
done

for f in "$ROOT"/agents/*.md; do
  deploy "$f" "$CURSOR/agents/$(basename "$f")"
done

echo "-- 完成 --"
[ -n "$DRY" ] && [ "$DRY" = "--dry" ] && echo "(dry-run，未写入)" && exit 0
echo "备份目录（如有覆盖）: $BACKUP_ROOT/$STAMP"
echo "生效：重启 ZCode / Cursor。验证："
echo "  ZCode : 输入 / 查看 Commands；Settings → Skills / Subagents"
echo "  Cursor: 输入 / 查看命令；@agent 引用 researcher/reviewer/architect"
