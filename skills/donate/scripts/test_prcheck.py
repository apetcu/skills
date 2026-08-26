import unittest

import prcheck as p


class Authors(unittest.TestCase):
    def test_bot_detection(self):
        self.assertTrue(p.is_bot({"login": "greptile-apps", "type": "Bot"}))
        self.assertTrue(p.is_bot({"login": "greptile-apps", "type": "User"}))  # known bot login
        self.assertTrue(p.is_bot({"login": "something[bot]", "type": "User"}))
        self.assertTrue(p.is_bot({"login": "CLAassistant", "type": "User"}))
        self.assertFalse(p.is_bot({"login": "maintainer", "type": "User"}))
        self.assertFalse(p.is_bot({}))

    def test_parse_pr_url(self):
        self.assertEqual(p.parse_pr_url("https://github.com/usestrix/strix/pull/1176"), ("usestrix", "strix", 1176))
        with self.assertRaises(ValueError):
            p.parse_pr_url("https://github.com/usestrix/strix/issues/1")


class Summarize(unittest.TestCase):
    CHECKS = [
        {"name": "tests", "status": "COMPLETED", "conclusion": "FAILURE"},
        {"name": "lint", "status": "COMPLETED", "conclusion": "SUCCESS"},
        {"name": "Greptile Review", "status": "IN_PROGRESS", "conclusion": None},
        {"context": "license/cla", "state": "PENDING"},  # StatusContext shape
    ]
    REVIEWS = [
        {"user": {"login": "greptile-apps", "type": "Bot"}, "state": "COMMENTED", "body": "2 issues found",
         "html_url": "r1"},
        {"user": {"login": "maintainer", "type": "User"}, "state": "CHANGES_REQUESTED", "body": "please split",
         "html_url": "r2"},
    ]
    REVIEW_COMMENTS = [
        {"user": {"login": "greptile-apps", "type": "Bot"}, "path": "a.py", "line": 12, "body": "possible None",
         "html_url": "c1", "id": 1},
        {"user": {"login": "maintainer", "type": "User"}, "path": "a.py", "line": 30, "body": "rename this",
         "html_url": "c2", "id": 2},
    ]
    ISSUE_COMMENTS = [
        {"user": {"login": "CLAassistant", "type": "User"}, "body": "Please sign the CLA", "html_url": "i1",
         "id": 3},
        {"user": {"login": "oss-account", "type": "User"}, "body": "my own note", "html_url": "i2", "id": 4},
    ]

    def test_classifies_checks_and_comments(self):
        s = p.summarize(self.CHECKS, self.REVIEWS, self.REVIEW_COMMENTS, self.ISSUE_COMMENTS, me="oss-account")
        self.assertEqual([c["name"] for c in s["failing_checks"]], ["tests"])
        self.assertEqual([c["name"] for c in s["pending_checks"]], ["Greptile Review", "license/cla"])
        self.assertEqual([c["author"] for c in s["bot_findings"]], ["greptile-apps", "greptile-apps", "CLAassistant"])
        self.assertEqual(s["bot_findings"][1]["where"], "a.py:12")
        self.assertEqual([c["author"] for c in s["human_comments"]], ["maintainer", "maintainer"])
        self.assertTrue(s["needs_cla"])
        self.assertTrue(s["actionable"])

    def test_quiet_pr_is_not_actionable(self):
        s = p.summarize([{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}], [], [], [], me="oss-account")
        self.assertFalse(s["actionable"])
        self.assertFalse(s["needs_cla"])
        self.assertEqual(s["human_comments"], [])


if __name__ == "__main__":
    unittest.main()
