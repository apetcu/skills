#!/usr/bin/env python3
"""star-history.com Weekly leaderboard (repos that gained the most stars this week) as JSON.

  leaderboard.py [--top N] [--html FILE] [--url URL]

Prints [{"rank": 1, "repo": "owner/name", "new_stars": 36922}, ...].
Exit 2 when the page markup is not recognised (star-history changed its HTML) — in that
case read the page yourself and pass repos explicitly with `/donate --repo owner/name`.
"""
import argparse
import json
import re
import sys
import urllib.request

URL = "https://www.star-history.com/"
UA = "Mozilla/5.0 (compatible; donate-skill)"

# The homepage server-renders the Weekly tab as <ol class="space-y-0.5"><li class="relative group">…
# Each <li> links to /owner/repo and carries a tooltip with the exact gain, e.g. "+36,922"
# (the visible label is rounded, "+36.9k", and never matches the digits-and-commas pattern).
_OL = re.compile(r'<ol class="space-y-0\.5">(.*?)</ol>', re.S)
_LI = re.compile(r'<li class="relative group">(.*?)</li>', re.S)
_HREF = re.compile(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"')
_STARS = re.compile(r"\+([\d,]+)</span>")


class ParseError(Exception):
    pass


def fetch_html(url=URL, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse_weekly(html):
    m = _OL.search(html)
    if not m:
        raise ParseError("weekly leaderboard <ol> not found")
    out = []
    for li in _LI.findall(m.group(1)):
        href = _HREF.search(li)
        if not href:
            continue
        stars = [int(s.replace(",", "")) for s in _STARS.findall(li)]
        out.append({"rank": len(out) + 1, "repo": href.group(1), "new_stars": max(stars) if stars else None})
    if not out:
        raise ParseError("weekly leaderboard has no entries")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--html", help="parse a saved HTML file instead of fetching")
    ap.add_argument("--url", default=URL)
    a = ap.parse_args(argv)
    try:
        if a.html:
            with open(a.html, encoding="utf-8") as f:
                html = f.read()
        else:
            html = fetch_html(a.url)
        repos = parse_weekly(html)[: a.top]
    except ParseError as e:
        print("leaderboard: %s. star-history markup may have changed; read %s manually and pass "
              "--repo owner/name to /donate." % (e, a.url), file=sys.stderr)
        return 2
    except Exception as e:  # network / IO
        print("leaderboard: fetch failed: %s" % e, file=sys.stderr)
        return 1
    json.dump(repos, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
