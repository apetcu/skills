#!/usr/bin/env bash
# Wipe $DONATE_HOME/work/*, optionally prune forks, restore the previous gh account, report disk + caches.
# Usage: cleanup.sh [--prune-forks] [--yes]     Env: DONATE_HOME (default ~/donate)
set -euo pipefail
DONATE_HOME="${DONATE_HOME:-$HOME/donate}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRUNE=0; YES=""
for a in "$@"; do
  case "$a" in
    --prune-forks) PRUNE=1 ;;
    --yes) YES="--yes" ;;
    -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
    *) echo "cleanup: unknown argument '$a'" >&2; exit 2 ;;
  esac
done

# Only ever delete inside a directory literally named donate*/work.
WORK="$DONATE_HOME/work"
case "$DONATE_HOME" in
  */donate|*/donate-*) ;;
  *) echo "cleanup: DONATE_HOME must be a directory named 'donate' or 'donate-*', got '$DONATE_HOME'" >&2; exit 1 ;;
esac
case "$WORK" in
  /|/work|"$HOME"|"$HOME/"|"$HOME/work") echo "cleanup: refusing to wipe '$WORK'" >&2; exit 1 ;;
esac

before="$(df -k "$HOME" | awk 'NR==2{print $4}')"
if [ -d "$WORK" ] && [ -n "$(ls -A "$WORK")" ]; then
  echo "cleanup: work dir was $(du -sh "$WORK" 2>/dev/null | cut -f1)"
  find "$WORK" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
fi
mkdir -p "$WORK"
after="$(df -k "$HOME" | awk 'NR==2{print $4}')"
echo "cleanup: freed $(( (after - before) / 1024 )) MB; $(( after / 1024 / 1024 )) GB free; work/ is empty"

# Prune while still on the contribution account (forks belong to it).
if [ "$PRUNE" = 1 ]; then
  python3 "$HERE/forks.py" prune $YES || echo "cleanup: fork pruning incomplete (see above)" >&2
fi

marker="$DONATE_HOME/.gh-previous-account"
if [ -f "$marker" ]; then
  prev="$(cat "$marker")"
  if [ -n "$prev" ] && gh auth switch --user "$prev" >/dev/null 2>&1; then
    echo "cleanup: gh account restored to $prev"
  else
    echo "cleanup: could not restore gh account '$prev' — run: gh auth switch --user $prev" >&2
  fi
  rm -f "$marker"
fi

echo "cleanup: shared caches (left untouched — prune by hand only if you need the space):"
for c in "$HOME/.npm" "$HOME/Library/pnpm" "$HOME/.cache/pnpm" "$HOME/.bun/install/cache" \
         "$HOME/.cache/uv" "$HOME/go/pkg/mod" "$HOME/.cargo/registry"; do
  if [ -d "$c" ]; then printf '  %s\t%s\n' "$(du -sh "$c" 2>/dev/null | cut -f1)" "$c"; fi
done
