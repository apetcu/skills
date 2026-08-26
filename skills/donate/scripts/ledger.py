#!/usr/bin/env python3
"""Ledger of every issue /donate has attempted, stored at $DONATE_HOME/ledger.json.

  ledger.py add --repo owner/name --issue N --status {pr_opened,abandoned,dry_run}
                [--pr-url URL] [--branch NAME] [--reason TEXT]
  ledger.py show [--repo owner/name]     human-readable table
  ledger.py attempted owner/name         issue numbers already attempted, one per line
  ledger.py prs                          "repo<TAB>pr_url" for every opened PR
"""
import argparse
import datetime
import json
import os
import sys

STATUSES = ("pr_opened", "abandoned", "dry_run")


def donate_home():
    return os.environ.get("DONATE_HOME") or os.path.expanduser("~/donate")


def ledger_path():
    return os.path.join(donate_home(), "ledger.json")


def contribution_account():
    """GitHub login that owns the PRs and forks: $DONATE_ACCOUNT, else DONATE_ACCOUNT=<login>
    in $DONATE_HOME/config. Raises LookupError when neither is set."""
    login = (os.environ.get("DONATE_ACCOUNT") or "").strip()
    if login:
        return login
    path = os.path.join(donate_home(), "config")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                key, _, value = line.strip().partition("=")
                if key.strip() == "DONATE_ACCOUNT" and value.strip():
                    return value.strip().strip("\"'")
    raise LookupError("no contribution account configured: set DONATE_ACCOUNT or write "
                      "DONATE_ACCOUNT=<login> to %s" % path)


def load(path=None):
    path = path or ledger_path()
    if not os.path.exists(path):
        return {"attempts": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("attempts", [])
    return data


def save(data, path=None):
    path = path or ledger_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)  # atomic: a crash mid-write never corrupts the ledger


def add(data, repo, issue, status, pr_url=None, branch=None, reason=None, date=None):
    if status not in STATUSES:
        raise ValueError("status must be one of %s" % (STATUSES,))
    entry = {
        "repo": repo,
        "issue": int(issue),
        "status": status,
        "pr_url": pr_url,
        "branch": branch,
        "reason": reason,
        "date": date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    data["attempts"].append(entry)
    return entry


def attempted(data, repo):
    """Issues already tried for real (PR opened or abandoned); dry runs don't consume an issue."""
    return sorted({a["issue"] for a in data["attempts"]
                   if a["repo"].lower() == repo.lower() and a["status"] != "dry_run"})


def opened_prs(data):
    return [(a["repo"], a["pr_url"]) for a in data["attempts"] if a["status"] == "pr_opened" and a.get("pr_url")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.required = True
    p = sub.add_parser("add")
    p.add_argument("--repo", required=True)
    p.add_argument("--issue", required=True, type=int)
    p.add_argument("--status", required=True, choices=STATUSES)
    p.add_argument("--pr-url")
    p.add_argument("--branch")
    p.add_argument("--reason")
    p = sub.add_parser("show")
    p.add_argument("--repo")
    p = sub.add_parser("attempted")
    p.add_argument("repo")
    sub.add_parser("prs")
    a = ap.parse_args(argv)

    data = load()
    if a.cmd == "add":
        entry = add(data, a.repo, a.issue, a.status, a.pr_url, a.branch, a.reason)
        save(data)
        print(json.dumps(entry))
    elif a.cmd == "show":
        rows = [x for x in data["attempts"] if not a.repo or x["repo"].lower() == a.repo.lower()]
        if not rows:
            print("(ledger empty)")
        for x in rows:
            print("%s  %-40s #%-6d %-9s %s" % (x["date"][:10], x["repo"], x["issue"], x["status"],
                                              x.get("pr_url") or x.get("reason") or ""))
    elif a.cmd == "attempted":
        for n in attempted(data, a.repo):
            print(n)
    elif a.cmd == "prs":
        for repo, url in opened_prs(data):
            print("%s\t%s" % (repo, url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
