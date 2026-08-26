import os
import tempfile
import unittest
import unittest.mock

import ledger


class Ledger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DONATE_HOME"] = os.path.join(self.tmp.name, "donate")

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("DONATE_HOME", None)

    def test_missing_file_loads_empty_ledger(self):
        self.assertEqual(ledger.load(), {"attempts": []})

    def test_roundtrip_attempted_and_opened_prs(self):
        d = ledger.load()
        ledger.add(d, "Owner/Repo", 12, "pr_opened", pr_url="https://github.com/owner/repo/pull/99",
                   branch="fix/12-crash", date="2026-08-26T00:00:00Z")
        ledger.add(d, "owner/repo", 13, "abandoned", reason="cannot reproduce", date="2026-08-26T00:00:00Z")
        ledger.save(d)
        d2 = ledger.load()
        self.assertEqual(ledger.attempted(d2, "owner/repo"), [12, 13])  # case-insensitive
        self.assertEqual(ledger.opened_prs(d2), [("Owner/Repo", "https://github.com/owner/repo/pull/99")])
        self.assertTrue(os.path.exists(ledger.ledger_path()))
        self.assertFalse(os.path.exists(ledger.ledger_path() + ".tmp"))

    def test_dry_runs_do_not_count_as_attempts(self):
        d = ledger.load()
        ledger.add(d, "a/b", 5, "dry_run", date="2026-08-26T00:00:00Z")
        ledger.add(d, "a/b", 6, "abandoned", reason="x", date="2026-08-26T00:00:00Z")
        self.assertEqual(ledger.attempted(d, "a/b"), [6])

    def test_contribution_account_from_env_then_config_file_else_error(self):
        with unittest.mock.patch.dict(os.environ, {"DONATE_ACCOUNT": "oss-account"}):
            self.assertEqual(ledger.contribution_account(), "oss-account")
        os.environ.pop("DONATE_ACCOUNT", None)
        with self.assertRaises(LookupError):
            ledger.contribution_account()
        os.makedirs(ledger.donate_home(), exist_ok=True)
        with open(os.path.join(ledger.donate_home(), "config"), "w", encoding="utf-8") as f:
            f.write("# donate settings\nDONATE_ACCOUNT = \"from-file\"\n")
        self.assertEqual(ledger.contribution_account(), "from-file")

    def test_add_stamps_utc_date_when_missing(self):
        e = ledger.add(ledger.load(), "a/b", "7", "dry_run")
        self.assertEqual(e["issue"], 7)
        self.assertRegex(e["date"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


if __name__ == "__main__":
    unittest.main()
