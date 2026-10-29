#!/usr/bin/env bash
# Link this library into Claude Code, Codex, the shared skill directory,
# and OpenCode.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$ROOT/skills" ]; then
  echo "skills/ not found next to install.sh" >&2
  exit 1
fi

link_tree() {
  local dest="$1"
  local skill name target
  mkdir -p "$dest"
  for skill in "$ROOT"/skills/*/; do
    [ -d "$skill" ] || continue
    name="$(basename "$skill")"
    target="${dest}/${name}"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      echo "skip $target (exists and is not a symlink)" >&2
      continue
    fi
    ln -sfn "$skill" "$target"
    echo "linked $target"
  done
}

link_files() {
  local src="$1"
  local dest="$2"
  local file name target
  [ -d "$src" ] || return 0
  mkdir -p "$dest"
  for file in "$src"/*; do
    [ -f "$file" ] || continue
    name="$(basename "$file")"
    target="${dest}/${name}"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      echo "skip $target (exists and is not a symlink)" >&2
      continue
    fi
    ln -sfn "$file" "$target"
    echo "linked $target"
  done
}

link_tree "${HOME}/.claude/skills"
link_tree "${HOME}/.codex/skills"
link_tree "${HOME}/.agents/skills"
link_files "$ROOT/opencode/agents" "${HOME}/.config/opencode/agents"
link_files "$ROOT/opencode/commands" "${HOME}/.config/opencode/commands"
