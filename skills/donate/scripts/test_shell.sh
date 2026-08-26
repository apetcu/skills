#!/usr/bin/env bash
# Exercises preflight.sh and cleanup.sh against a temp DONATE_HOME with a stubbed `gh`.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat > "$TMP/bin/gh" <<'EOS'
#!/usr/bin/env bash
echo "$*" >> "$GH_LOG"
case "$*" in
  "api user --jq .login") cat "$GH_LOGIN_FILE";;
  "api user --jq .id") echo 4242;;
  "api user --jq .name // .login") echo "Adrian";;
  auth\ switch*) all="$*"; echo "${all##* }" > "$GH_LOGIN_FILE";;
esac
EOS
chmod +x "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH" GH_LOG="$TMP/gh.log" GH_LOGIN_FILE="$TMP/login" DONATE_HOME="$TMP/donate"
echo "work-account" > "$GH_LOGIN_FILE"
fail() { echo "FAIL: $*" >&2; exit 1; }

# no account configured → preflight refuses, nothing switched
unset DONATE_ACCOUNT
if "$HERE/preflight.sh" >/dev/null 2>&1; then fail "preflight ran without a configured account"; fi
[ "$(cat "$GH_LOGIN_FILE")" = "work-account" ] || fail "preflight switched without config"

# account from $DONATE_HOME/config: switches, remembers previous account, creates dirs, prints JSON
mkdir -p "$DONATE_HOME"; echo 'DONATE_ACCOUNT=oss-account' > "$DONATE_HOME/config"
out="$("$HERE/preflight.sh")"
[ "$(cat "$GH_LOGIN_FILE")" = "oss-account" ] || fail "preflight did not switch account"
[ "$(cat "$DONATE_HOME/.gh-previous-account")" = "work-account" ] || fail "previous account not recorded"
echo "$out" | grep -q '"email":"4242+oss-account@users.noreply.github.com"' || fail "preflight json missing email: $out"
echo "$out" | grep -q '"login":"oss-account"' || fail "preflight json missing login"
echo "$out" | grep -q '"count":5,"max_pr_per_repo":1,"top":15' || fail "preflight json missing default settings: $out"

# settings from config + env override; unlimited is reported as a word
printf 'DONATE_ACCOUNT=oss-account\nDONATE_COUNT=unlimited\nDONATE_TOP=20\n' > "$DONATE_HOME/config"
out="$(DONATE_MAX_PR_PER_REPO=2 "$HERE/preflight.sh")"
echo "$out" | grep -q '"count":"unlimited","max_pr_per_repo":2,"top":20' || fail "preflight json settings wrong: $out"
printf 'DONATE_ACCOUNT=oss-account\n' > "$DONATE_HOME/config"
[ -d "$DONATE_HOME/work" ] && [ -d "$DONATE_HOME/runs" ] || fail "dirs not created"

# preflight is idempotent: already on the account → no marker overwrite
"$HERE/preflight.sh" >/dev/null
[ "$(cat "$DONATE_HOME/.gh-previous-account")" = "work-account" ] || fail "second preflight clobbered marker"

# cleanup: wipes work/*, keeps work/, restores account, clears marker
mkdir -p "$DONATE_HOME/work/owner__repo/node_modules/x"; echo junk > "$DONATE_HOME/work/owner__repo/node_modules/x/f"
"$HERE/cleanup.sh" >/dev/null
[ -d "$DONATE_HOME/work" ] || fail "work dir removed entirely"
[ -z "$(ls -A "$DONATE_HOME/work")" ] || fail "work dir not empty"
[ "$(cat "$GH_LOGIN_FILE")" = "work-account" ] || fail "account not restored"
[ ! -f "$DONATE_HOME/.gh-previous-account" ] || fail "previous-account marker not cleared"

# guard: refuses to treat $HOME as the workspace
mkdir -p "$TMP/home/work"; echo keep > "$TMP/home/work/keep"
if HOME="$TMP/home" DONATE_HOME="$TMP/home" "$HERE/cleanup.sh" >/dev/null 2>&1; then fail "cleanup accepted DONATE_HOME=\$HOME"; fi
[ -f "$TMP/home/work/keep" ] || fail "guard deleted files"
echo "shell tests: OK"
