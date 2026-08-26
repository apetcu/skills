#!/usr/bin/env bash
# Prepare $DONATE_HOME for a run: switch gh to the contribution account (remembering the previous one),
# create work/ and runs/, snapshot free disk. Prints one JSON line.
# Env: DONATE_HOME (default ~/donate). Settings (env > $DONATE_HOME/config > defaults):
#   DONATE_ACCOUNT (required), DONATE_COUNT (5 or "unlimited"), DONATE_MAX_PR_PER_REPO (1), DONATE_TOP (15)
set -euo pipefail
DONATE_HOME="${DONATE_HOME:-$HOME/donate}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
settings="$(python3 "$HERE/ledger.py" config --shell)" || { echo "preflight: invalid settings (see above)" >&2; exit 2; }
eval "$settings"
ACCOUNT="$DONATE_ACCOUNT"
if [ -z "$ACCOUNT" ]; then
  echo "preflight: no contribution account configured — set DONATE_ACCOUNT or write DONATE_ACCOUNT=<login> to $DONATE_HOME/config" >&2
  exit 2
fi
mkdir -p "$DONATE_HOME/work" "$DONATE_HOME/runs"

prev="$(gh api user --jq .login 2>/dev/null || true)"
if [ "$prev" != "$ACCOUNT" ]; then
  # remember who was active so cleanup.sh can switch back; never clobber an existing marker
  if [ -n "$prev" ] && [ ! -f "$DONATE_HOME/.gh-previous-account" ]; then
    echo "$prev" > "$DONATE_HOME/.gh-previous-account"
  fi
  gh auth switch --user "$ACCOUNT" >/dev/null
fi
login="$(gh api user --jq .login)"
if [ "$login" != "$ACCOUNT" ]; then
  echo "preflight: gh is authenticated as '$login', expected '$ACCOUNT' (run: gh auth login -u $ACCOUNT)" >&2
  exit 1
fi
id="$(gh api user --jq .id)"
name="$(gh api user --jq '.name // .login')"
free_kb="$(df -k "$HOME" | awk 'NR==2{print $4}')"
leftover="$(ls -A "$DONATE_HOME/work" | wc -l | tr -d ' ')"
count_json="$DONATE_COUNT"; [ "$count_json" = "unlimited" ] && count_json='"unlimited"'
printf '{"login":"%s","email":"%s+%s@users.noreply.github.com","name":"%s","previous_account":"%s","donate_home":"%s","free_gb":%d,"leftover_workdirs":%d,"count":%s,"max_pr_per_repo":%d,"top":%d}\n' \
  "$login" "$id" "$login" "$name" "$prev" "$DONATE_HOME" "$((free_kb / 1024 / 1024))" "$leftover" "$count_json" "$DONATE_MAX_PR_PER_REPO" "$DONATE_TOP"
