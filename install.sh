#!/usr/bin/env bash
# Installs creative-factory into your Claude Code skills directory.
# Override the destination with:  CLAUDE_SKILLS_DIR=/custom/path ./install.sh
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="$SKILLS_DEST/creative-factory"

mkdir -p "$SKILLS_DEST"
if [ -e "$DEST" ]; then
  echo "! creative-factory already exists at $DEST — remove it first to reinstall."
  exit 1
fi
mkdir -p "$DEST"
cp -R "$REPO_DIR"/SKILL.md "$REPO_DIR"/scripts "$REPO_DIR"/references "$REPO_DIR"/assets "$REPO_DIR"/evals "$DEST"/
echo "✓ installed creative-factory → $DEST"
echo
echo "The compliance gate uses the brand-system skill if installed; otherwise it falls back to the"
echo "vendored copy in this repo. For the full closed loop, also install the companion portfolio skills."
echo
echo "In Claude Code it triggers by intent, e.g. \"generate on-brand ad variants for Meta and LinkedIn\"."
