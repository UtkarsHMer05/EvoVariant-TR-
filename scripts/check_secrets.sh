#!/bin/bash
# Secret scanner for EvoVariant-TR (Milestone 19).
#
# Scans all git-tracked files for credential-looking assignments and bare token
# shapes. Excludes *.example files (names-only templates). Exit 0 = clean,
# 1 = findings, 2 = usage/repo error.
#
# Usage: ./scripts/check_secrets.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not a git repository" >&2
  exit 2
fi

PATTERNS=(
  # key=value where the value looks like a real (long) secret token.
  # The 16-char minimum excludes code identifiers (e.g. `_SECRET_QUERY_KEYS =
  # frozenset(`) and short test fixtures while still catching real credentials.
  '(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|CREDENTIAL)[A-Z0-9_]*[[:space:]]*=[[:space:]]*["'"'"']?[A-Za-z0-9_-]{16,}'
  # Require a token boundary so slugs such as "mask-resolution-20260922"
  # do not look like an OpenAI-style key.
  '(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{16,}'
  'ghp_[A-Za-z0-9]{20,}'
  'AKIA[0-9A-Z]{16}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
)

findings=0
for pattern in "${PATTERNS[@]}"; do
  # -I skips binaries; exclude names-only templates and this scanner itself.
  if matches=$(git grep -nIE "$pattern" -- . ':!*.example' ':!scripts/check_secrets.sh' ':!docs/security/*' 2>/dev/null); then
    if [[ -n "$matches" ]]; then
      echo "FINDING (pattern: $pattern):"
      echo "$matches"
      findings=$((findings + 1))
    fi
  fi
done

if [[ "$findings" -gt 0 ]]; then
  echo ""
  echo "FAIL: $findings secret pattern(s) found in tracked files."
  echo "Remove the secret, rotate it, and purge it from history before committing."
  exit 1
fi

echo "OK: no secret patterns found in tracked files."
exit 0
