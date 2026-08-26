import unittest

from leaderboard import ParseError, parse_weekly

# Minimal replica of the star-history.com homepage Weekly list markup (Aug 2026).
FIXTURE = """<a href="/coding-ai-leaderboard">Coding AI Leaderboard</a>
<ol class="space-y-0.5">
<li class="relative group"><a href="/deepseek-ai/deepseek-harness" class="flex"><span>1</span>
<span class="truncate">deepseek-harness</span><span class="text-xs accent-text">+36.9k</span></a>
<span class="hidden z-10">deepseek-ai/deepseek-harness<!-- --> <!-- -->+36,922</span></li>
<li class="relative group"><a href="/mattpocock/skills" class="flex"><span>2</span>
<span class="truncate">skills</span><span class="text-xs accent-text">+15.1k</span></a>
<span class="hidden z-10">mattpocock/skills<!-- --> <!-- -->+15,146</span></li>
</ol>
<ol class="other"><li class="relative group"><a href="/not/this">x</a></li></ol>"""


class ParseWeekly(unittest.TestCase):
    def test_parses_rank_repo_and_exact_star_gain(self):
        self.assertEqual(
            parse_weekly(FIXTURE),
            [
                {"rank": 1, "repo": "deepseek-ai/deepseek-harness", "new_stars": 36922},
                {"rank": 2, "repo": "mattpocock/skills", "new_stars": 15146},
            ],
        )

    def test_raises_when_markup_changes(self):
        with self.assertRaises(ParseError):
            parse_weekly("<html><ol class='other'><li>nothing</li></ol></html>")

    def test_raises_when_list_is_empty(self):
        with self.assertRaises(ParseError):
            parse_weekly('<ol class="space-y-0.5"></ol>')


if __name__ == "__main__":
    unittest.main()
