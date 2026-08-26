import unittest
import unittest.mock

import forks


class Prunable(unittest.TestCase):
    def test_only_repos_whose_prs_are_all_closed_and_have_a_known_fork(self):
        states = {"a/x": ["MERGED"], "b/y": ["OPEN", "MERGED"], "c/z": ["CLOSED"], "d/w": ["MERGED"]}
        fmap = {"a/x": "me/x", "b/y": "me/y", "c/z": "me/z-1"}
        self.assertEqual(forks.prunable(states, fmap), ["me/x", "me/z-1"])

    def test_repo_match_is_case_insensitive(self):
        self.assertEqual(forks.prunable({"A/X": ["MERGED"]}, {"a/x": "me/x"}), ["me/x"])

    def test_unknown_state_blocks_pruning(self):
        self.assertEqual(forks.prunable({"a/x": ["UNKNOWN"]}, {"a/x": "me/x"}), [])


if __name__ == "__main__":
    unittest.main()


class ForkMap(unittest.TestCase):
    def test_parses_gh_repo_list_parent_shape(self):
        rows = [{"name": "strix", "parent": {"name": "strix", "owner": {"login": "usestrix"}}},
                {"name": "skills-1", "parent": {"name": "skills", "owner": {"login": "Some-Org"}}},
                {"name": "orphan", "parent": None}]
        with unittest.mock.patch.object(forks, "gh", return_value=__import__("json").dumps(rows)):
            self.assertEqual(forks.fork_map("me"), {"usestrix/strix": "me/strix", "some-org/skills": "me/skills-1"})
