#!/usr/bin/env python3
"""What happened on our PRs: failing/pending checks, bot findings, human comments.

  prcheck.py <pr-url> [<pr-url> ...] [--json]
  prcheck.py --from-ledger [--hours 24] [--json]

Bots are review bots (Greptile, Copilot, CodeRabbit, ...), CI apps and CLA/DCO checkers.
Human comments are listed so the user can answer them; the skill never replies to humans.
Comments by the contribution account ($DONATE_ACCOUNT or ~/donate/config) are ignored.
"""
import argparse
import datetime
import json
import re
import subprocess
import sys

import ledger

KNOWN_BOTS = {
    "greptile-apps", "copilot-pull-request-reviewer", "copilot", "coderabbitai", "sonarcloud", "sonarqubecloud",
    "codecov", "codecov-commenter", "claassistant", "cla-assistant", "cla-bot", "dco", "dependabot",
    "github-actions", "vercel", "netlify", "codesandbox-ci", "sentry-io", "cursor", "gemini-code-assist",
    "devin-ai-integration", "sourcery-ai", "ellipsis-dev", "pr-agent", "codiumai-pr-agent", "graphite-app",
    "mergify", "renovate", "semgrep", "snyk-bot", "deepsource-autofix", "codeclimate", "pull-request-size",
}
FAILED = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "ERROR", "STARTUP_FAILURE"}
CLA_RE = re.compile(r"\b(cla|contributor license agreement|dco|sign-?off)\b", re.I)


def is_bot(user):
    login = (user or {}).get("login") or ""
    if not login:
        return False
    lowered = login.lower()
    return user.get("type") == "Bot" or lowered.endswith("[bot]") or lowered in KNOWN_BOTS


def parse_pr_url(url):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not m:
        raise ValueError("not a pull request url: %s" % url)
    return m.group(1), m.group(2), int(m.group(3))


def _check_state(check):
    """statusCheckRollup mixes CheckRun (status/conclusion) and StatusContext (state) shapes."""
    name = check.get("name") or check.get("context") or "?"
    if "status" in check or "conclusion" in check:
        if (check.get("status") or "").upper() != "COMPLETED":
            return name, "pending"
        return name, "failed" if (check.get("conclusion") or "").upper() in FAILED else "passed"
    state = (check.get("state") or "").upper()
    if state in ("", "PENDING", "EXPECTED"):
        return name, "pending"
    return name, "failed" if state in FAILED else "passed"


def summarize(checks, reviews, review_comments, issue_comments, me):
    buckets = {"failed": [], "pending": [], "passed": []}
    for c in checks or []:
        name, state = _check_state(c)
        buckets[state].append({"name": name, "state": state})
    bots, humans = [], []

    def add(kind, item, where=None):
        user = item.get("user") or item.get("author") or {}
        login = user.get("login") or "?"
        if login.lower() == (me or "").lower():
            return
        entry = {"kind": kind, "author": login, "where": where, "state": item.get("state"),
                 "body": (item.get("body") or "").strip(), "url": item.get("html_url"), "id": item.get("id")}
        (bots if is_bot(user) else humans).append(entry)

    for r in reviews or []:
        if (r.get("body") or "").strip() or r.get("state") in ("CHANGES_REQUESTED", "APPROVED"):
            add("review", r)
    for c in review_comments or []:
        add("inline", c, "%s:%s" % (c.get("path"), c.get("line") or c.get("original_line") or "?"))
    for c in issue_comments or []:
        add("comment", c)
    needs_cla = any(CLA_RE.search(b["body"]) for b in bots) or \
        any(CLA_RE.search(c["name"]) for c in buckets["failed"] + buckets["pending"])
    real_findings = [b for b in bots if not CLA_RE.search(b["body"])]
    return {"failing_checks": buckets["failed"], "pending_checks": buckets["pending"],
            "passed_checks": buckets["passed"], "bot_findings": bots, "human_comments": humans,
            "needs_cla": needs_cla, "actionable": bool(buckets["failed"] or real_findings)}


# ---------------------------------------------------------------- gh-backed

def gh_json(*args):
    r = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("gh %s: %s" % (" ".join(args), r.stderr.strip()[:300]))
    return json.loads(r.stdout) if r.stdout.strip() else None


def collect(url):
    owner, repo, number = parse_pr_url(url)
    pr = gh_json("pr", "view", url, "--json", "state,statusCheckRollup,headRefName,reviewDecision,mergeable")
    base = "repos/%s/%s" % (owner, repo)
    reviews = gh_json("api", base + "/pulls/%d/reviews?per_page=100" % number) or []
    review_comments = gh_json("api", base + "/pulls/%d/comments?per_page=100" % number) or []
    issue_comments = gh_json("api", base + "/issues/%d/comments?per_page=100" % number) or []
    return pr, reviews, review_comments, issue_comments


def report(url, pr, summary):
    lines = ["## %s  (%s, branch %s, review=%s)" % (url, pr.get("state"), pr.get("headRefName"),
                                                     pr.get("reviewDecision") or "none")]
    lines.append("checks: %d passed, %d failed, %d pending%s" % (
        len(summary["passed_checks"]), len(summary["failing_checks"]), len(summary["pending_checks"]),
        "  FAILED: " + ", ".join(c["name"] for c in summary["failing_checks"]) if summary["failing_checks"] else ""))
    for label, items in (("bot findings", summary["bot_findings"]), ("human comments", summary["human_comments"])):
        lines.append("%s (%d):" % (label, len(items)))
        for it in items:
            body = " ".join(it["body"].split())
            lines.append("  - %s %s%s [id %s]\n      %s\n      %s" % (
                it["author"], it["kind"], " " + it["where"] if it["where"] else "", it["id"], body[:400], it["url"]))
    lines.append("needs CLA: %s · actionable: %s" % ("yes" if summary["needs_cla"] else "no",
                                                    "yes" if summary["actionable"] else "no"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--from-ledger", action="store_true", help="PRs opened per the ledger")
    ap.add_argument("--hours", type=float, default=24, help="with --from-ledger: only PRs opened within N hours")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    urls = list(a.urls)
    if a.from_ledger:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=a.hours)
        for e in ledger.load()["attempts"]:
            if e["status"] == "pr_opened" and e.get("pr_url"):
                when = datetime.datetime.strptime(e["date"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                if when >= cutoff and e["pr_url"] not in urls:
                    urls.append(e["pr_url"])
    if not urls:
        print("prcheck: no PRs to check", file=sys.stderr)
        return 1
    try:
        me = ledger.contribution_account()
    except LookupError as e:
        print("prcheck: %s" % e, file=sys.stderr)
        return 2
    results = []
    for url in urls:
        try:
            pr, reviews, rc, ic = collect(url)
            summary = summarize(pr.get("statusCheckRollup") or [], reviews, rc, ic, me)
            results.append({"url": url, "pr": pr, **summary})
            if not a.json:
                print(report(url, pr, summary))
                print()
        except Exception as e:  # keep checking the others
            results.append({"url": url, "error": str(e)[:300]})
            if not a.json:
                print("## %s\nerror: %s\n" % (url, e))
    if a.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
