---
paths:
  - "docs/rules/git.md"
---

# Git

## Authorship

**Commits are the repository owner's.** No `Co-Authored-By` trailer, no assistant named as author
or co-author, no "generated with" line, no session link, nothing in the message about how the work
was produced.

`git log` records who is responsible for the code, and that is a person. An AI wrote part of it the
way an editor or a linter did — that is not authorship, and it makes the history harder to read.

The same applies to a pull request description.

## Messages

Written in English, like everything else here.

- Subject line in the imperative, under about 60 characters: `Add token refresh job`, not
  `Added token refresh job` or `token stuff`.
- A blank line, then a body explaining **why**, wrapped near 80 characters. What changed is in the
  diff; the reason is not.
- **Keep the body short — about five lines, ten at the most.** One reason, not a report. If it
  reads like a summary of the work, delete it and say the one thing that is not in the diff.
- Reasoning that outlives the commit belongs in `docs/structure-decisions.md` or a `CLAUDE.md`,
  where it will be read again. A long commit message is written once and found by nobody.
- One logical change per commit. A refactor and a feature in one commit cannot be reverted apart.

## Assume another agent is editing this checkout

The working tree is shared; the commit is not.

**Never `git add -A`, never `git add .`, never `git commit -a`.** Name the paths on the commit
itself:

```
git commit src/media/ tests/media/ docs/api/media.md
```

**Staging by name is not enough.** `git commit` commits the whole index, not the paths you just
added — so whatever somebody else staged in another terminal rides along under your message. A
pathspec on `git commit` bypasses the index and commits exactly those files.

If you stage first anyway, read `git diff --cached --stat` before committing and account for every
path in it.

Before staging, `git status` and account for every changed path. A file you did not touch is
somebody else's — leave it unstaged, even when it is obviously an improvement and even when it is
one line.

The same applies in reverse: do not revert, stash, reformat or "tidy" a file outside your task.
`git checkout --` and `git stash` throw away work that may not be yours.

## What never gets committed

`.env`, `logs/`, `media/`, `db.sqlite3`, `__pycache__/`, `.venv/`, `.idea/` — see `.gitignore`.

`.env.example` **is** committed, carrying every key with an empty value. A key added to `.env`
without being added there is a deployment that fails on somebody else's machine.

`.claude/rules` is a symlink to `docs/rules` and **must stay committed as a symlink**. Claude Code
loads rules from `.claude/rules/`; delete or flatten it and every rule silently stops loading.
`.claude/` is therefore not in `.gitignore` — only `.claude/settings.local.json` is.

## A leaked token is not fixed by a second commit

`git rm` and an amend do not remove anything already pushed, and a token in history is a token
somebody else has. The order is: **rotate at Meta first**, then clean the history, then talk about
whether the rewrite is worth it. Deleting the line and moving on is the one response that does
nothing.

## Before committing

- `uv run pytest` passes.
- `uv run manage.py makemigrations --check --dry-run` reports no changes.
- `docs/rules/structure.md` matches the tree, and every `CLAUDE.md` you touched matches its
  directory.
- **No secret in the diff.** `git diff --cached` before committing, every time — an access token,
  an app secret, a `.env`, a fixture with a real value.
