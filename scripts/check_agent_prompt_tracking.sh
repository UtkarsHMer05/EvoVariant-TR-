#!/usr/bin/env bash
set -euo pipefail

matches="$(git ls-files | rg -i '(^|/)(\.agent-prompts/|\.codex/|CODEX_MASTER_PROMPT\.md$|.*codex.*prompt.*\.md$|.*AGENT_PROMPT.*\.md$)' || true)"
if [[ -n "$matches" ]]; then
  echo "ERROR: local coding-agent prompt files are tracked:" >&2
  echo "$matches" >&2
  exit 1
fi
echo "OK: no local coding-agent prompt files are tracked"
