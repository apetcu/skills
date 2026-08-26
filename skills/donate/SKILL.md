---
name: donate
description: "Use when the user wants to donate engineering time to trending open-source projects — says /donate, 'contribute to open source', 'fix some issues in popular repos', 'open a few PRs to the star-history top projects' — or wants the ~/donate workspace cleaned up or old contribution forks pruned."
---

# Donate

Fix a handful of small, verifiable bugs in the repos currently trending on
[star-history.com](https://www.star-history.com/) (Weekly leaderboard), open PRs from the
personal GitHub account, and leave the machine exactly as you found it.

**Core principle:** small verified fixes from the right identity, and nothing left on disk.
A run that opens 3 clean PRs and deletes every clone beats one that opens 5 sloppy ones.

`S` below is this skill's `scripts/` directory (`<skill base dir>/scripts`). All scripts are
stdlib Python 3.9 / bash and print `--help`.

## Invocation

| Command | Effect |
|---|---|
| `/donate` | top 15 weekly repos → up to 5 PRs |
| `/donate --count 3` | stop after 3 PRs |
| `/donate --top 20` | consider more repos |
| `/donate --repo owner/name` | skip discovery, work only in that repo |
| `/donate --dry-run` | everything except fork/push/PR; fixes saved as `.patch` files |
| `/donate --followup` | re-check the PRs opened in the last 24 h for bot/CI feedback, act on it, then exit |
| `/donate --prune-forks` | delete forks whose PRs are all merged/closed, then exit |
| `/donate --keep` | don't delete clones (debugging only) |

## Workflow

### 0. Preflight

```bash
eval "$(bash $S/preflight.sh | python3 -c 'import json,sys; d=json.load(sys.stdin); print(" ".join("%s=%r"%(k.upper(),v) for k,v in d.items()))')"
# → LOGIN EMAIL NAME PREVIOUS_ACCOUNT DONATE_HOME FREE_GB LEFTOVER_WORKDIRS
```

`preflight.sh` switches `gh` to the **contribution account** — `DONATE_ACCOUNT` in the
environment, or `DONATE_ACCOUNT=<login>` in `~/donate/config` — and records the account that was
active so `cleanup.sh` can switch back. **First run:** if preflight reports no account
configured, ask the user which GitHub account the contributions should come from (a personal
account, not an employer-linked one), write `DONATE_ACCOUNT=<login>` to `~/donate/config`, and
re-run preflight. `LOGIN`, `NAME` and `EMAIL` (the account's noreply address) come from its output. If `LEFTOVER_WORKDIRS > 0` a previous run died: run
`bash $S/cleanup.sh` first. If `FREE_GB < 10`, stop and tell the user — don't start a run that
will fail mid-install. Record `FREE_GB` for the report. `RUN=~/donate/runs/$(date +%Y-%m-%dT%H-%M)`.

`--prune-forks`: `python3 $S/forks.py prune` (needs a TTY or `--yes`), then `bash $S/cleanup.sh`, report, stop.

### 1. Discover

```bash
python3 $S/leaderboard.py --top 15 > $RUN-leaderboard.json
```

Exit 2 means star-history changed its markup: read https://www.star-history.com/ yourself,
take the **Weekly** tab's top entries (not All-time), and continue with `--repos`. Never
substitute `gh search repos --sort=stars` — that is the all-time list, not this week's.

### 2. Triage

```bash
python3 $S/candidates.py --leaderboard $RUN-leaderboard.json --login "$LOGIN" --max-per-repo 5 > $RUN-candidates.json
```

The script already drops archived repos, repos without a fully open license (see Guardrails),
docs/list repos, repos whose toolchain isn't installed, repos that prohibit AI-assisted
contributions, repos where `$LOGIN` already has an open PR, and
issues that are assigned, linked to a PR, labeled as feature/question/discussion, older than 90
days, over 15 comments, or too short to contain a repro. It never substitutes judgment for
reading: for each `status: ok` repo, open the top issues with
`gh issue view N --repo R --comments` and build a **queue of ~8 issues, max 2 per repo**,
ordered by how confident you are that the fix is small and testable. If `ai_policy` is
`disclose`, the disclosure line in the PR body is mandatory (it is always present anyway).

### 3. Fix loop — one issue at a time, sequentially

Set `OWNER REPO N SLUG DEFAULT` (default branch from candidates.json), then:

```bash
W=~/donate/work/${OWNER}__${REPO}
FORK=$(gh repo fork "$OWNER/$REPO" --clone=false 2>&1 | grep -oE "$LOGIN/[A-Za-z0-9_.-]+" | head -1)
git clone -q --filter=blob:none "git@github.com:$FORK.git" "$W" && cd "$W"
git config user.name "$NAME" && git config user.email "$EMAIL"      # local config only
git remote add upstream "https://github.com/$OWNER/$REPO.git" && git fetch -q upstream "$DEFAULT"
git checkout -q -b "fix/$N-$SLUG" "upstream/$DEFAULT"
```

Install only what the repo's lockfile says (`pnpm install --frozen-lockfile` / `npm ci` /
`yarn install --frozen-lockfile` / `bun install`; Python: `uv venv .venv && uv pip install -e
".[dev]"` falling back to `-e .` + `requirements*-dev.txt`; Go and Rust need nothing up front).
Check `du -sh "$W"` after install; over 5 GB → abandon.

Then, in this order:

1. **Reproduce** — find the code path from the issue; run the existing test or a one-off script
   that shows the bug. Can't reproduce → abandon.
2. **Failing test** — when the repo has a suite, add the smallest test that fails for this bug.
3. **Fix** — minimal diff, same style as surrounding code, no drive-by refactors.
4. **Format** — run the repo's formatter/linter on touched files only.
5. **Verify** — run the targeted tests (touched package/file) and the new test; they must pass.
   Read `CONTRIBUTING.md` for the real commands and any DCO (`git commit -s`) or commit-message
   convention (`git log --oneline -15` shows it).
6. **Last check** — `gh pr list --repo $OWNER/$REPO --search "$N in:body" --state open` still
   empty; otherwise abandon (someone got there first).
7. **Commit, push, PR** (skip push/PR under `--dry-run`, see below):

```bash
git add -A && git commit -q -m "<repo convention>: <one line>"       # add -s if CONTRIBUTING says DCO
git push -q -u origin "fix/$N-$SLUG"
gh pr create --repo "$OWNER/$REPO" --base "$DEFAULT" --head "$LOGIN:fix/$N-$SLUG" \
  --title "<repo convention>: <one line>" --body-file "$RUN-pr-$N.md"
python3 $S/ledger.py add --repo "$OWNER/$REPO" --issue "$N" --status pr_opened --pr-url "<url>" --branch "fix/$N-$SLUG"
cd ~/donate && rm -rf "$W"                                            # immediately, not at the end
```

**Dry run:** no fork — clone `https://github.com/$OWNER/$REPO.git` directly, do everything up
to the commit, then `git diff "upstream/$DEFAULT" > "$RUN-$OWNER__$REPO-$N.patch"` and confirm
`git apply --stat` on that file lists your files (a shell hook that filters command output can
leave you with an unusable patch), ledger status `dry_run`, delete the clone. **`--keep`:** skip only the `rm -rf`.

**PR body** (`$RUN-pr-$N.md`). If the repo has a PR template, keep its headings and fill them;
otherwise use exactly this:

```markdown
## Summary
<what was broken, one or two sentences>

Fixes #<N>

## Root cause
<one to three sentences>

## Changes
- <one bullet per behavior/file>

## Verification
- `<exact test command>` — passes; <new test / previously failing>
- <manual check, if any>

---
Prepared with AI assistance (Claude Code); reviewed and tested locally by @<LOGIN>.
```

**Abandon** (ledger `abandoned --reason "<why>"`, `rm -rf "$W"`, next issue) when any holds:
can't reproduce · fix needs > 5 files or > 150 lines or a public-API/architecture change ·
tests need secrets, Docker, GPU or external services · install > 5 GB or fails twice · a PR for
the issue appeared · 45 minutes in and the fix is still speculative. Abandoning is normal;
the queue has slack for it.

Stop the loop when `--count` PRs are open or the queue is empty.

### 4. Cleanup — always, even after errors

```bash
bash $S/cleanup.sh            # wipes ~/donate/work/*, restores the previous gh account, reports caches
ls -A ~/donate/work           # must print nothing
gh api user --jq .login       # must be the account preflight reported as previous_account
```

Shared caches (`~/.npm`, pnpm store, `~/.cache/uv`, `~/go/pkg/mod`, `~/.cargo/registry`) are
reported, never pruned — other projects depend on them. Forks are kept: deleting a fork closes
its open PRs. `/donate --prune-forks` removes them once their PRs are merged or closed.

### 5. Follow-up — 10 minutes after the last PR

Bots (Greptile, Copilot, CodeRabbit, CLA/DCO checkers, CI) comment a few minutes after a PR
opens. Wait for them without polling: start `sleep 600` in the background and continue when it
returns (never cut the wait short because "nothing has shown up yet"). Then switch `gh` back
with `bash $S/preflight.sh` and:

```bash
python3 $S/prcheck.py --from-ledger --hours 24      # per PR: failing/pending checks, bot findings, human comments
```

For each PR that is `actionable`:
- **Failing check or bot finding** → open the code it points at and decide whether it is right;
  bots are wrong often enough that "the bot said so" is never a reason to change code. If right:
  re-clone the branch (`git clone -q --filter=blob:none -b "fix/$N-$SLUG" "git@github.com:$FORK.git" "$W"`,
  set the local `user.name`/`user.email` again), fix, run the targeted tests, push, then reply on
  the thread: `gh api repos/$OWNER/$REPO/pulls/$PR/comments/$COMMENT_ID/replies -f body="Addressed in <sha>."`
  (inline comment) or `gh pr comment <url> --body "..."` (review/issue comment). If wrong: reply
  in one sentence why and leave the code alone.
- **CLA / DCO bot** (`needs_cla`) → nothing to fix; it goes under "Needs you".
- **Human comment** → goes under "Needs you". Don't answer maintainers under the user's name.

Delete the clone again and run `bash $S/cleanup.sh`. `/donate --followup` runs only this section.

### 6. Report — save to `$RUN.md` and print it

```markdown
# /donate <timestamp>
## PRs opened (<n>/<count>)
| repo | license | issue | PR | verified with |
## Abandoned / skipped
| repo | issue | reason |
## Follow-up (T+10 min)
| PR | checks | bot findings | action taken |
## Disk
<FREE_GB> GB free before → <now> GB after · work/ empty ✓ · gh account restored to <previous_account> ✓
## Forks held (until PRs close)
<from `python3 $S/forks.py list`> — prune later with `/donate --prune-forks`
## Needs you
<CLA bots to sign, maintainer questions, anything that requires the human>
```

## Guardrails

- **Only fully open licenses.** `candidates.py` allows OSI-approved licenses (MIT, Apache-2.0,
  BSD, ISC, MPL, EPL, GPL/LGPL/AGPL, Unlicense, CC0, …) and skips source-available (BUSL, SSPL,
  Elastic, FSL, PolyForm), custom (`Other`) and unlicensed repos. This keeps contributions clear
  of employment conflicts — never override a license skip, and `--repo` targets get the same
  check (`gh api repos/O/R --jq .license.spdx_id`).
- PRs, commits and forks belong to the contribution account (`$LOGIN` from preflight), never to
  whatever account happened to be active. Never `git config --global`; never push to `upstream`;
  never force-push; never open more than one PR per repo per run.
- Delete only inside `~/donate/work`. Never touch global package caches or other checkouts.
- Every PR: reproduced, tested, minimal, links its issue, carries the AI-assistance line.
- Respect repo policy: `ai_policy: ban` repos are skipped by the script — don't override it;
  DCO and commit conventions come from `CONTRIBUTING.md`, not from habit.
- Sequential, one clone at a time. Parallel clones multiply disk use on a 95%-full drive.

## Red flags — stop and re-read the step

| Thought | Reality |
|---|---|
| "I'll set `git config --global user.email`" | Local config per clone; preflight gave you `NAME`/`EMAIL`. |
| "Whatever `gh` account is active is fine" | An employer-linked account could end up owning the PRs. Preflight switches to `DONATE_ACCOUNT`, cleanup restores. |
| "star-history has no canonical list, I'll use `gh search --sort=stars`" | That's all-time. Use `leaderboard.py` or the Weekly tab by hand. |
| "Most-commented issues are the important ones" | Long threads are contested. Prefer reproducible, low-comment bugs. |
| "I'll purge pnpm/npm/go/pip caches to free space" | Shared with other projects. Report only. |
| "Skip the disclosure, maintainers may not like it" | It stays. Repos that ban AI work are skipped instead. |
| "PR is open, delete the fork too" | Deleting the fork closes the PR. Prune only after merge/close. |
| "I'll clean up all clones at the end" | Disk is nearly full. `rm -rf "$W"` right after each PR. |
| "Tests are slow, the fix is obvious, ship it" | Run the targeted tests. No green, no PR. |
| "License is 'Other' but the code is public, it's fine" | Public ≠ open. Not on the allowlist → skip. |
| "No bot comments after 3 minutes, skip the rest of the wait" | Bots take up to 10 minutes. Let the timer finish. |
| "The bot flagged it, so I'll change it" | Read the code first. Reply why when the bot is wrong. |
