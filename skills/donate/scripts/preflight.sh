#!/usr/bin/env bash
# Prepare $DONATE_HOME for a run: switch gh to the contribution account (remembering the previous one),
# create work/ and runs/, snapshot free disk. Prints one JSON line.
# Env: DONATE_HOME (default ~/donate); DONATE_ACCOUNT, else DONATE_ACCOUNT=<login> in $DONATE_HOME/config
set -euo pipefail
DONATE_HOME="${DONATE_HOME:-$HOME/donate}"
ACCOUNT="${DONATE_ACCOUNT:-}"
if [ -z "$ACCOUNT" ] && [ -f "$DONATE_HOME/config" ]; then
  ACCOUNT="$(sed -n 's/^[[:space:]]*DONATE_ACCOUNT[[:space:]]*=[[:space:]]*//p' "$DONATE_HOME/config" | tail -1 | tr -d '"'"'"' ')"
fi
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
printf '{"login":"%s","email":"%s+%s@users.noreply.github.com","name":"%s","previous_account":"%s","donate_home":"%s","free_gb":%d,"leftover_workdirs":%d}\n' \
  "$login" "$id" "$login" "$name" "$prev" "$DONATE_HOME" "$((free_kb / 1024 / 1024))" "$leftover"
