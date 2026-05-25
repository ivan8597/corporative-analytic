#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_SRC="$ROOT/scripts/git-hooks"
HOOKS_DST="$ROOT/.git/hooks"

mkdir -p "$HOOKS_DST"
for hook in prepare-commit-msg commit-msg; do
  cp "$HOOKS_SRC/$hook" "$HOOKS_DST/$hook"
  chmod +x "$HOOKS_DST/$hook"
done
echo "Git hooks installed in $HOOKS_DST"
