#!/usr/bin/env bash
# Agent OS 同步脚本：本仓库（单一事实源）→ 本机任意 Agent 工具
# 内容层（AGENTS.md / commands / skills / agents）全部是通用 Markdown，
# 本脚本只负责一件事：把它们复制进各家工具的约定目录。
# 用法：bash sync.sh              自动检测本机已安装的工具并部署
#       bash sync.sh --dry        预览将部署什么，不写入
#       bash sync.sh --target a,b 只部署指定工具（名字见 --list）
#       bash sync.sh --all        部署到全部已知工具（含未检测到的）
#       bash sync.sh --list       列出支持的工具与部署路径
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_ROOT="${AGENT_OS_BACKUP:-$HOME/.agent-os-backup}"
CFG_BASE="${XDG_CONFIG_HOME:-$HOME/.config}"
DRY=0; ALL=0; LIST=0; TARGETS=""

# 工具映射表：name|工具目录|规则文件|规则形态|commands目录|skills目录|agents目录
# 规则形态：plain = AGENTS.md 原样复制；mdc = 生成 Cursor .mdc（带 alwaysApply frontmatter）
# 目录为 "-" 表示该工具无此概念，跳过。适配新工具 = 加一行映射，不改其他代码。
TOOL_TABLE="zcode|$HOME/.zcode|AGENTS.md|plain|commands|skills|agents
claude|$HOME/.claude|CLAUDE.md|plain|commands|skills|agents
cursor|$HOME/.cursor|rules/agent-os.mdc|mdc|commands|skills|agents
codex|$HOME/.codex|AGENTS.md|plain|prompts|-|-
gemini|$HOME/.gemini|GEMINI.md|plain|-|-|-
opencode|$CFG_BASE/opencode|AGENTS.md|plain|commands|skills|agents"

usage() { sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --dry) DRY=1; shift ;;
    --all) ALL=1; shift ;;
    --list) LIST=1; shift ;;
    --target) TARGETS="${2:-}"; [ -n "$TARGETS" ] || { echo "--target 需要参数（见 --list）"; exit 2; }; shift 2 ;;
    --target=*) TARGETS="${1#--target=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1"; usage; exit 2 ;;
  esac
done

# deploy <src> <dst> —— 内容有变化才覆盖；覆盖前备份旧文件
deploy() {
  local src="$1" dst="$2"
  local rel="${dst#$HOME/}"
  if [ "$DRY" = 1 ]; then
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

deploy_tool() { # name home rules style cmds skills agents
  local name="$1" home="$2" rules="$3" style="$4" cmds="$5" skills="$6" agents="$7"
  echo "-- $name ($home) --"
  case "$style" in
    plain) deploy "$ROOT/AGENTS.md" "$home/$rules" ;;
    mdc)
      # 核心规则：AGENTS.md 正文 + Cursor .mdc frontmatter（始终生效）
      local mdc; mdc="$(mktemp)"
      {
        printf -- '---\n'
        printf 'description: Agent OS 核心工作规则（理解→选择→执行→验证→交付）\n'
        printf 'alwaysApply: true\n'
        printf -- '---\n\n'
        tail -n +2 "$ROOT/AGENTS.md"   # 跳过标题行，保留规则正文
      } > "$mdc"
      deploy "$mdc" "$home/$rules"
      rm -f "$mdc"
      ;;
  esac
  if [ "$cmds" != "-" ]; then
    local f
    for f in "$ROOT"/commands/*.md; do [ -e "$f" ] || continue
      deploy "$f" "$home/$cmds/$(basename "$f")"
    done
  fi
  if [ "$skills" != "-" ]; then
    local d name2
    for d in "$ROOT"/skills/*/; do [ -e "$d" ] || continue
      name2="$(basename "$d")"
      deploy "$d/SKILL.md" "$home/$skills/$name2/SKILL.md"
    done
  fi
  if [ "$agents" != "-" ]; then
    local f2
    for f2 in "$ROOT"/agents/*.md; do [ -e "$f2" ] || continue
      deploy "$f2" "$home/$agents/$(basename "$f2")"
    done
  fi
}

tool_names() { echo "$TOOL_TABLE" | awk -F'|' '{print $1}'; }

tool_line() { # name -> 输出映射表匹配行（名字唯一）
  echo "$TOOL_TABLE" | awk -F'|' -v n="$1" '$1 == n {print; exit}'
}

if [ "$LIST" = 1 ]; then
  echo "支持的工具（bash sync.sh --target 名1,名2 指定部署）："
  echo "$TOOL_TABLE" | awk -F'|' -v h="$HOME" \
    'BEGIN{printf "%-10s %-6s %-34s %-10s %-6s %-6s %s\n","工具","已装","全局规则","Commands","Skills","Agents","工具目录"}
     {det=($2!=""&&system("test -d \""$2"\"")==0)?"是":"-";
      gsub(h"/","~/",$2);
      printf "%-10s %-6s %-34s %-10s %-6s %-6s %s\n",$1,det,$3,($5=="-"?"-":$5),($6=="-"?"-":$6),($7=="-"?"-":$7),$2}'
  exit 0
fi

echo "== Agent OS sync =="
[ "$DRY" = 1 ] && echo "(dry-run 预览，未写入)"

SELECTED=""
SKIPPED=""
while IFS='|' read -r name home rules style cmds skills agents; do
  [ -n "$name" ] || continue
  if [ -n "$TARGETS" ]; then
    case ",$TARGETS," in *",$name,"*) ;; *) continue ;; esac
  elif [ "$ALL" != 1 ]; then
    if [ ! -d "$home" ]; then SKIPPED="$SKIPPED $name"; continue; fi
  fi
  deploy_tool "$name" "$home" "$rules" "$style" "$cmds" "$skills" "$agents"
  SELECTED="$SELECTED $name"
done <<< "$TOOL_TABLE"

if [ -z "$SELECTED" ]; then
  echo "!! 未部署任何工具。"
  [ -n "$TARGETS" ] && echo "   检查 --target 名称（bash sync.sh --list 查看）"
  echo "   默认只部署本机已安装的工具；用 --all 强制全部，或 --target 指定。"
  exit 1
fi
[ -n "$SKIPPED" ] && echo "未检测到（已跳过）:$SKIPPED —— 可用 --target 显式指定"

if [ "$DRY" = 1 ]; then
  echo "-- 完成（dry-run，未写入）--"
  exit 0
fi
echo "-- 完成 --"
echo "备份目录（如有覆盖）: $BACKUP_ROOT/$STAMP"
echo "生效：重启对应工具。验证：输入 / 应看到 plan、research、debug、review、verify、html、inbox 命令；"
echo "Skills / Subagents 在各工具的对应设置页查看。"
