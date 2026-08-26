#!/usr/bin/env python3
"""Forks held by the contribution account, driven by the ledger.

  forks.py list            every opened PR: repo, state, url, fork
  forks.py prune [--yes]   delete forks whose ledger PRs are ALL merged/closed (gh must be on that account)

The account is $DONATE_ACCOUNT (or ~/donate/config), not whichever gh account is active.

A fork must stay while any PR from it is open: GitHub closes a PR when its head fork is deleted.
"""
import argparse
import json
import subprocess
import sys
from collections import defaultdict

import ledger

DONE = {"MERGED", "CLOSED"}


def prunable(pr_states, fork_map):
    """pr_states: {repo: [state, ...]}; fork_map: {parent_lower: fork_full}.
    Returns forks of repos whose PRs are all done."""
    out = []
    for repo, states in pr_states.items():
        if states and all(s in DONE for s in states) and repo.lower() in fork_map:
            out.append(fork_map[repo.lower()])
    return out


def gh(*args):
    r = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("gh %s: %s" % (" ".join(args), r.stderr.strip()[:300]))
    return r.stdout


def fork_map(login):
    """{parent 'owner/name' lower-cased: 'login/fork-name'} for every fork the account holds."""
    rows = json.loads(gh("repo", "list", login, "--fork", "--limit", "200", "--json", "name,parent") or "[]")
    out = {}
    for r in rows:
        parent = r.get("parent") or {}
        owner = (parent.get("owner") or {}).get("login")
        if owner and parent.get("name"):
            out[("%s/%s" % (owner, parent["name"])).lower()] = "%s/%s" % (login, r["name"])
    return out


def pr_state(url):
    try:
        return gh("pr", "view", url, "--json", "state", "--jq", ".state").strip() or "UNKNOWN"
    except RuntimeError:
        return "UNKNOWN"


def collect(login):
    states, rows = defaultdict(list), []
    fmap = fork_map(login)
    for repo, url in ledger.opened_prs(ledger.load()):
        st = pr_state(url)
        states[repo].append(st)
        rows.append((repo, url, st, fmap.get(repo.lower(), "-")))
    return rows, states, fmap


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.required = True
    sub.add_parser("list")
    p = sub.add_parser("prune")
    p.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)

    try:
        login = ledger.contribution_account()
    except LookupError as e:
        print("forks: %s" % e, file=sys.stderr)
        return 2
    rows, states, fmap = collect(login)
    if a.cmd == "list":
        if not rows:
            print("(no PRs in ledger)")
        for repo, url, st, fork in rows:
            print("%-40s %-8s %s  fork=%s" % (repo, st, url, fork))
        return 0

    targets = prunable(states, fmap)
    if not targets:
        print("prune: nothing to prune (ledger PRs still open, or no matching forks)")
        return 0
    print("prune: forks whose PRs are all merged/closed:")
    for t in targets:
        print("  " + t)
    if not a.yes:
        if not sys.stdin.isatty():
            print("prune: re-run with --yes to delete", file=sys.stderr)
            return 1
        if input("delete these forks? [y/N] ").strip().lower() != "y":
            return 1
    rc = 0
    for t in targets:
        try:
            gh("repo", "delete", t, "--yes")
            print("deleted " + t)
        except RuntimeError as e:
            rc = 1
            print("could not delete %s: %s" % (t, e), file=sys.stderr)
            if "delete_repo" in str(e) or "scope" in str(e):
                print("hint: gh auth refresh -h github.com -s delete_repo", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
