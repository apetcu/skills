#!/usr/bin/env python3
"""Rank repos and their open issues for /donate.

  candidates.py --repos owner/a,owner/b [--max-per-repo 5] [--login LOGIN] [--days 90]
  candidates.py --leaderboard leaderboard.json ...

Requires an authenticated `gh`. Prints JSON:
{"login": "...", "repos": [{"repo", "status": "ok"|"skipped"|"error", "reason", "license", "toolchain",
   "ai_policy", "ai_policy_snippet", "default_branch", "stars",
   "issues": [{"number","title","url","score","reasons","labels","comments","created_at"}]}]}
"""
import argparse
import base64
import datetime
import json
import re
import shutil
import subprocess
import sys
import time

import ledger

TOOLCHAINS = {"JavaScript": "node", "TypeScript": "node", "Vue": "node", "Svelte": "node",
              "Python": "python3", "Go": "go", "Rust": "cargo"}
MIN_CODE_BYTES = 20000  # below this GitHub's language bytes say "list / docs repo"
MIN_SCORE = 3  # an issue needs at least a bug/GFI/help label or a repro to be worth reading
# Fully open (OSI-approved) licenses only. Source-available (BUSL, SSPL, Elastic, FSL, PolyForm),
# custom ("Other"/NOASSERTION) and unlicensed repos are skipped so contributions stay clear of
# employment conflicts.
OPEN_LICENSES = {
    "MIT", "MIT-0", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "ISC", "Unlicense", "Zlib",
    "MPL-2.0", "EPL-1.0", "EPL-2.0", "CDDL-1.0", "PostgreSQL", "BSL-1.0", "Artistic-2.0", "EUPL-1.2",
    "GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0", "CC0-1.0", "Python-2.0", "OFL-1.1",
}
EXCLUDE_LABELS = {"question", "discussion", "enhancement", "feature", "feature request", "feature-request",
                  "wontfix", "won't fix", "needs-info", "needs info", "needs more info", "duplicate", "invalid",
                  "stale", "epic", "tracking", "roadmap", "design", "proposal", "rfc", "documentation", "docs"}
BUG_LABELS = ("bug", "kind/bug", "type: bug", "type:bug", "t-bug", "defect", "regression", "crash")
GFI_LABELS = ("good first issue", "good-first-issue", "beginner", "easy", "starter", "first-timers-only")
HELP_LABELS = ("help wanted", "help-wanted", "contributions welcome", "up for grabs", "pr welcome")
REPRO_WORDS = ("steps to reproduce", "to reproduce", "reproduction", "stack trace", "traceback",
               "expected behavior", "expected behaviour", "actual behavior", "actual behaviour", "minimal repro")
FEATURE_TITLE = re.compile(r"^\s*\[?\s*(?:feature|feat|proposal|rfc|idea|discussion)\b|\bfeature request\b", re.I)

AI_WORDS = r"(?:ai|llm|llms|chatgpt|copilot|claude|cursor|ai-generated|ai-assisted|machine.generated)"
AI_BAN = re.compile(
    r"\b(?:not accept|don'?t accept|do not accept|prohibit(?:ed|s)?|reject(?:ed|s)?|ban(?:ned)?|forbid(?:den)?|"
    r"will be closed|not allowed|not welcome)\b[^.\n]{0,80}\b" + AI_WORDS + r"\b"
    r"|\bno\s+" + AI_WORDS + r"\b"
    r"|\b" + AI_WORDS + r"\b[^.\n]{0,80}\b(?:not accepted|not allowed|prohibited|forbidden|will be closed|"
    r"are banned|is banned|not welcome|rejected|will be rejected)\b", re.I)
AI_DISCLOSE = re.compile(
    r"\b(?:disclose|disclosure|declare|indicate|mention|state|label|note)\b[^.\n]{0,80}\b" + AI_WORDS + r"\b"
    r"|\b" + AI_WORDS + r"\b[^.\n]{0,60}\b(?:disclos\w*|declar\w*)\b", re.I)


# ---------------------------------------------------------------- pure logic

def classify_ai_policy(text):
    """Return (policy, snippet) where policy is "ban", "disclose" or "none"."""
    if not text:
        return "none", ""
    m = AI_BAN.search(text)
    if m:
        return "ban", " ".join(m.group(0).split())
    m = AI_DISCLOSE.search(text)
    if m:
        return "disclose", " ".join(m.group(0).split())
    return "none", ""


def detect_toolchain(languages):
    """languages = GET /repos/{r}/languages. Returns (tool name, available locally)."""
    if not languages:
        return None, False
    top = max(languages, key=languages.get)
    tool = TOOLCHAINS.get(top)
    return tool, bool(tool and shutil.which(tool))


def repo_license(info):
    return (info.get("license") or {}).get("spdx_id")


def repo_skip_reason(info, languages, toolchain_ok, ai_policy, our_open_prs):
    if info.get("archived"):
        return "archived"
    spdx = repo_license(info)
    if not spdx or spdx == "NOASSERTION":
        return "no license or unrecognized license (not fully open)"
    if spdx not in OPEN_LICENSES:
        return "license %s is not a fully open (OSI-approved) license" % spdx
    if not info.get("has_issues", True):
        return "issues disabled"
    if sum(languages.values()) < MIN_CODE_BYTES:
        return "no meaningful code (docs/list repo)"
    if not toolchain_ok:
        return "no local toolchain for %s" % max(languages, key=languages.get)
    if ai_policy == "ban":
        return "repo prohibits AI-assisted contributions"
    if our_open_prs:
        return "we already have %d open PR(s) here" % our_open_prs
    return None


def _label_names(issue):
    names = set()
    for label in issue.get("labels") or []:
        names.add((label.get("name") if isinstance(label, dict) else str(label)).lower())
    return names


def _has(labels, wanted):
    return any(re.search(r"\b%s\b" % re.escape(w), l) for l in labels for w in wanted)


def score_issue(issue, now=None):
    """Return (score, reasons) or None when the issue should be excluded outright."""
    if issue.get("pull_request"):
        return None
    labels = _label_names(issue)
    if labels & EXCLUDE_LABELS:
        return None
    if (issue.get("comments") or 0) > 15:
        return None
    body = issue.get("body") or ""
    if len(body) < 150:
        return None
    is_bug = _has(labels, BUG_LABELS)
    if FEATURE_TITLE.search(issue.get("title") or "") and not is_bug:
        return None

    score, reasons = 0, []
    if is_bug:
        score += 3
        reasons.append("bug label")
    if _has(labels, GFI_LABELS):
        score += 3
        reasons.append("good first issue")
    if _has(labels, HELP_LABELS):
        score += 2
        reasons.append("help wanted")
    lowered = body.lower()
    if any(w in lowered for w in REPRO_WORDS):
        score += 2
        reasons.append("has repro")
    if "```" in body:
        score += 1
        reasons.append("code/log block")
    if ((issue.get("reactions") or {}).get("total_count") or 0) >= 3:
        score += 1
        reasons.append("reactions")
    now = now or datetime.datetime.now(datetime.timezone.utc)
    updated = issue.get("updated_at")
    if updated:
        when = datetime.datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        if (now - when).days <= 14:
            score += 1
            reasons.append("active")
    if (issue.get("comments") or 0) > 8:
        score -= 1
        reasons.append("long thread")
    return score, reasons


# ---------------------------------------------------------------- gh-backed

RATE_LIMITED = re.compile(r"rate limit", re.I)


def gh(*args, **kw):
    """Run gh; on GitHub's (secondary) rate limit wait 30s, 60s, 90s before giving up."""
    retries = kw.get("retries", 3)
    for attempt in range(retries + 1):
        r = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
        if RATE_LIMITED.search(r.stderr) and attempt < retries:
            wait = 30 * (attempt + 1)
            print("candidates: GitHub rate limit hit, waiting %ds" % wait, file=sys.stderr)
            time.sleep(wait)
            continue
        raise RuntimeError("gh %s: %s" % (" ".join(args), r.stderr.strip()[:300]))


def gh_json(*args):
    out = gh(*args)
    return json.loads(out) if out.strip() else None


def _decode_contents(d):
    if isinstance(d, dict) and d.get("encoding") == "base64":
        return base64.b64decode(d["content"]).decode("utf-8", "replace")
    return ""


def repo_policy_text(repo):
    """CONTRIBUTING + PR template text. The community-profile endpoint tells us where they live,
    so this costs 1-3 requests instead of probing six paths."""
    try:
        files = (gh_json("api", "repos/%s/community/profile" % repo) or {}).get("files") or {}
    except RuntimeError:
        return ""
    parts = []
    for key in ("contributing", "pull_request_template"):
        entry = files.get(key)
        if entry and entry.get("url"):
            try:
                parts.append(_decode_contents(gh_json("api", entry["url"])))
            except RuntimeError:
                pass
    return "\n".join(parts)


def search_issues(repo, days):
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    q = "repo:%s is:issue is:open no:assignee -linked:pr created:>=%s" % (repo, since)
    d = gh_json("api", "-X", "GET", "search/issues", "-f", "q=" + q, "-f", "per_page=100", "-f", "sort=updated")
    return (d or {}).get("items", [])


def our_open_pr_count(repo, login):
    return len(gh_json("pr", "list", "--repo", repo, "--author", login, "--state", "open", "--json", "number") or [])


def evaluate_repo(repo, login, days, max_per_repo, attempted):
    # Cheap metadata first; the policy-file fetches and searches only run for repos that survive.
    info = gh_json("api", "repos/" + repo)
    languages = gh_json("api", "repos/%s/languages" % repo) or {}
    tool, tool_ok = detect_toolchain(languages)
    out = {"repo": repo, "status": "ok", "reason": None, "license": repo_license(info), "toolchain": tool,
           "ai_policy": None, "ai_policy_snippet": "", "default_branch": info.get("default_branch"),
           "stars": info.get("stargazers_count"), "issues": []}
    reason = repo_skip_reason(info, languages, tool_ok, "none", 0)
    if reason:
        out.update(status="skipped", reason=reason)
        return out
    policy, snippet = classify_ai_policy(repo_policy_text(repo))
    out.update(ai_policy=policy, ai_policy_snippet=snippet)
    reason = repo_skip_reason(info, languages, tool_ok, policy, our_open_pr_count(repo, login))
    if reason:
        out.update(status="skipped", reason=reason)
        return out
    scored = []
    for it in search_issues(repo, days):
        if it["number"] in attempted:
            continue
        s = score_issue(it)
        if s is None or s[0] < MIN_SCORE:
            continue
        scored.append({"number": it["number"], "title": it["title"], "url": it["html_url"], "score": s[0],
                       "reasons": s[1], "labels": sorted(_label_names(it)), "comments": it.get("comments", 0),
                       "created_at": it.get("created_at")})
    scored.sort(key=lambda x: (-x["score"], x["comments"]))
    out["issues"] = scored[:max_per_repo]
    if not scored:
        out.update(status="skipped", reason="no suitable open issues")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--repos", help="comma-separated owner/name list")
    g.add_argument("--leaderboard", help="JSON file produced by leaderboard.py")
    ap.add_argument("--max-per-repo", type=int, default=5)
    ap.add_argument("--login", help="GitHub login used for PRs (default: the contribution account, else gh api user)")
    ap.add_argument("--days", type=int, default=90, help="only issues created within N days")
    ap.add_argument("--pause", type=float, default=2.0, help="seconds to wait between repos (rate limits)")
    a = ap.parse_args(argv)

    if a.repos:
        repos = [r.strip() for r in a.repos.split(",") if r.strip()]
    else:
        with open(a.leaderboard, encoding="utf-8") as f:
            repos = [x["repo"] for x in json.load(f)]
    login = a.login
    if not login:
        try:
            login = ledger.contribution_account()
        except LookupError:
            login = gh("api", "user", "--jq", ".login").strip()
    data = ledger.load()
    results = []
    for i, repo in enumerate(repos):
        if i and a.pause:
            time.sleep(a.pause)
        print("candidates: %s" % repo, file=sys.stderr)
        try:
            results.append(evaluate_repo(repo, login, a.days, a.max_per_repo, set(ledger.attempted(data, repo))))
        except Exception as e:  # one bad repo must not sink the run
            results.append({"repo": repo, "status": "error", "reason": str(e)[:300], "issues": []})
    json.dump({"login": login, "repos": results}, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
