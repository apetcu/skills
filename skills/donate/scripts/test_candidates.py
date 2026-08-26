import datetime
import unittest
from unittest import mock

import candidates as c

NOW = datetime.datetime(2026, 8, 26, tzinfo=datetime.timezone.utc)
BODY = ("Steps to reproduce:\n1. run x\n2. see crash\n\nExpected behavior: no crash\nActual: TypeError\n"
        "```\nTraceback (most recent call last)\n```\n" + "x" * 100)


def issue(**kw):
    base = {"number": 1, "title": "Crash when config is empty", "labels": [{"name": "bug"}], "comments": 2,
            "body": BODY, "html_url": "u", "updated_at": "2026-08-25T00:00:00Z",
            "reactions": {"total_count": 0}}
    base.update(kw)
    return base


class ScoreIssue(unittest.TestCase):
    def test_bug_gfi_repro_scores_high_with_reasons(self):
        score, reasons = c.score_issue(issue(labels=[{"name": "bug"}, {"name": "good first issue"}]), now=NOW)
        self.assertGreaterEqual(score, 8)
        for r in ("bug label", "good first issue", "has repro", "active"):
            self.assertIn(r, reasons)

    def test_excludes_enhancement_label(self):
        self.assertIsNone(c.score_issue(issue(labels=[{"name": "enhancement"}]), now=NOW))

    def test_excludes_short_body(self):
        self.assertIsNone(c.score_issue(issue(body="too short"), now=NOW))

    def test_excludes_long_threads(self):
        self.assertIsNone(c.score_issue(issue(comments=16), now=NOW))

    def test_excludes_feature_request_titles(self):
        self.assertIsNone(c.score_issue(issue(title="Feature request: dark mode", labels=[]), now=NOW))

    def test_keeps_bug_whose_title_merely_contains_request(self):
        self.assertIsNotNone(c.score_issue(issue(title="Request timeout is ignored"), now=NOW))

    def test_excludes_pull_requests(self):
        self.assertIsNone(c.score_issue(issue(pull_request={"url": "x"}), now=NOW))


class AiPolicy(unittest.TestCase):
    def test_ban(self):
        self.assertEqual(c.classify_ai_policy("We do not accept AI-generated pull requests.")[0], "ban")

    def test_ban_reverse_order(self):
        self.assertEqual(c.classify_ai_policy("PRs written by LLM tools will be closed without review.")[0], "ban")

    def test_disclose(self):
        self.assertEqual(c.classify_ai_policy("Please disclose any use of AI tools in your PR.")[0], "disclose")

    def test_none(self):
        self.assertEqual(c.classify_ai_policy("Run the tests before opening a PR."), ("none", ""))

    def test_empty(self):
        self.assertEqual(c.classify_ai_policy(""), ("none", ""))


class Toolchain(unittest.TestCase):
    def test_top_language_maps_to_tool(self):
        with mock.patch("shutil.which", return_value="/usr/bin/node"):
            self.assertEqual(c.detect_toolchain({"TypeScript": 9000, "CSS": 100}), ("node", True))

    def test_unknown_language(self):
        self.assertEqual(c.detect_toolchain({"Haskell": 5000}), (None, False))

    def test_empty(self):
        self.assertEqual(c.detect_toolchain({}), (None, False))


class RepoSkip(unittest.TestCase):
    OK = {"archived": False, "has_issues": True, "license": {"spdx_id": "MIT"}}
    LANGS = {"Python": 50000}

    def test_ok(self):
        self.assertIsNone(c.repo_skip_reason(self.OK, self.LANGS, True, "none", 0))

    def test_archived(self):
        self.assertEqual(c.repo_skip_reason({"archived": True, "has_issues": True}, self.LANGS, True, "none", 0), "archived")

    def test_issues_disabled(self):
        info = {"archived": False, "has_issues": False, "license": {"spdx_id": "MIT"}}
        self.assertEqual(c.repo_skip_reason(info, self.LANGS, True, "none", 0), "issues disabled")

    def test_docs_only(self):
        self.assertIn("no meaningful code", c.repo_skip_reason(self.OK, {"Shell": 5000}, True, "none", 0))

    def test_no_toolchain(self):
        self.assertIn("toolchain", c.repo_skip_reason(self.OK, self.LANGS, False, "none", 0))

    def test_ai_ban(self):
        self.assertIn("prohibits", c.repo_skip_reason(self.OK, self.LANGS, True, "ban", 0))

    def test_existing_pr(self):
        self.assertIn("open PR", c.repo_skip_reason(self.OK, self.LANGS, True, "none", 1))


if __name__ == "__main__":
    unittest.main()


class RateLimitRetry(unittest.TestCase):
    def _run(self, outcomes):
        calls = []

        def fake_run(args, **kw):
            calls.append(args)
            rc, err = outcomes[min(len(calls) - 1, len(outcomes) - 1)]
            return mock.Mock(returncode=rc, stdout='{"ok": true}' if rc == 0 else "", stderr=err)

        with mock.patch("subprocess.run", side_effect=fake_run), mock.patch("time.sleep") as sleep:
            return calls, sleep, c.gh_json("api", "x")

    def test_retries_after_secondary_rate_limit(self):
        calls, sleep, out = self._run([(1, "gh: You have exceeded a secondary rate limit. Please wait"), (0, "")])
        self.assertEqual(out, {"ok": True})
        self.assertEqual(len(calls), 2)
        sleep.assert_called_once()

    def test_gives_up_after_retries(self):
        with self.assertRaises(RuntimeError):
            self._run([(1, "API rate limit exceeded")])

    def test_no_retry_on_other_errors(self):
        with self.assertRaises(RuntimeError):
            calls, sleep, _ = self._run([(1, "gh: Not Found (HTTP 404)")])


class ShortCircuit(unittest.TestCase):
    def test_archived_repo_skips_policy_fetch_and_search(self):
        def fake_gh_json(*a):
            return {"archived": True, "has_issues": True, "default_branch": "main"} if a[1] == "repos/o/r" else {}

        with mock.patch.object(c, "gh_json", side_effect=fake_gh_json), \
                mock.patch.object(c, "repo_policy_text") as policy, \
                mock.patch.object(c, "search_issues") as search, \
                mock.patch.object(c, "our_open_pr_count") as prs:
            out = c.evaluate_repo("o/r", "me", 90, 5, set())
        self.assertEqual(out["status"], "skipped")
        policy.assert_not_called()
        search.assert_not_called()
        prs.assert_not_called()


class MinScoreAndPolicyFetch(unittest.TestCase):
    def test_low_scoring_issues_do_not_make_a_repo_ok(self):
        weak = issue(labels=[], body="x" * 200, title="Add my API to the list", updated_at="2026-01-01T00:00:00Z")

        def fake_gh_json(*a):
            if a[1] == "repos/o/r":
                return {"archived": False, "has_issues": True, "default_branch": "main",
                        "license": {"spdx_id": "MIT"}}
            return {"Python": 50000}

        with mock.patch.object(c, "gh_json", side_effect=fake_gh_json), \
                mock.patch.object(c, "repo_policy_text", return_value=""), \
                mock.patch.object(c, "our_open_pr_count", return_value=0), \
                mock.patch.object(c, "search_issues", return_value=[weak]), \
                mock.patch("shutil.which", return_value="/usr/bin/python3"):
            out = c.evaluate_repo("o/r", "me", 90, 5, set())
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out["reason"], "no suitable open issues")

    def test_policy_text_uses_community_profile_links_only(self):
        import base64
        profile = {"files": {"contributing": {"url": "https://api.github.com/repos/o/r/contents/CONTRIBUTING.md"},
                             "pull_request_template": None, "readme": {"url": "https://api.github.com/x/README.md"}}}
        blob = {"encoding": "base64", "content": base64.b64encode(b"Please disclose AI usage").decode()}
        calls = []

        def fake_gh_json(*a):
            calls.append(a[1])
            return profile if a[1].endswith("/community/profile") else blob

        with mock.patch.object(c, "gh_json", side_effect=fake_gh_json):
            text = c.repo_policy_text("o/r")
        self.assertIn("disclose AI usage", text)
        self.assertEqual(calls, ["repos/o/r/community/profile", "https://api.github.com/repos/o/r/contents/CONTRIBUTING.md"])


class LicenseGate(unittest.TestCase):
    OK = {"archived": False, "has_issues": True}
    LANGS = {"Python": 50000}

    def _info(self, spdx):
        return {"archived": False, "has_issues": True, "license": {"spdx_id": spdx} if spdx else None}

    def test_osi_licenses_pass(self):
        for spdx in ("MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0", "GPL-3.0", "AGPL-3.0", "ISC"):
            self.assertIsNone(c.repo_skip_reason(self._info(spdx), self.LANGS, True, "none", 0), spdx)

    def test_source_available_is_skipped(self):
        for spdx in ("BUSL-1.1", "SSPL-1.0", "Elastic-2.0", "Other"):
            self.assertIn("license", c.repo_skip_reason(self._info(spdx), self.LANGS, True, "none", 0), spdx)

    def test_missing_or_unrecognized_license_is_skipped(self):
        self.assertIn("no license", c.repo_skip_reason(self._info(None), self.LANGS, True, "none", 0))
        self.assertIn("no license", c.repo_skip_reason(self._info("NOASSERTION"), self.LANGS, True, "none", 0))

    def test_legacy_repo_skip_fixture_without_license_key_is_skipped(self):
        # older callers that pass no license information must not sneak past the gate
        self.assertIn("no license", c.repo_skip_reason(self.OK, self.LANGS, True, "none", 0))
