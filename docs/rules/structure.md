---
paths:
  - "docs/rules/structure.md"
  - "scripts/check-docs.sh"
---

# Structure

The map of this repository, as it is **right now**.

This file describes what exists. It never describes what is planned, intended or coming later.
A reader must be able to trust that every path listed here is real, and that anything not listed
does not exist. Planned structure belongs in `docs/structure-decisions.md`, never here.

## The rule

**A file added, deleted, renamed or moved is not done until this file reflects it, in the same change.**

- File created → add the line.
- File deleted → remove the line.
- File renamed or moved → move the line, do not leave the old one.
- Directory created or removed → same.

## How to update it

1. **Never write the tree from memory.** Ask the checker what is wrong:

   ```
   ./scripts/check-docs.sh
   ```

   It parses the tree below into real paths and compares them with the repository, so it reports
   a path that exists but is not listed — **and which two entries it goes between** — an entry
   listed but gone, an entry listed twice, and an entry out of order. Copy the indentation from the
   neighbour it names; you do not have to read the tree to add a line to it.

   It checks four more things: what every `CLAUDE.md` under `src/` **claims** (the model count
   against `models.py`, `no services` / `no selectors` against the files, any endpoint count
   against the `path(` calls under that directory), whether every routed path reached a
   `docs/api/**.md`, whether every page there is named on the map in `docs/api/README.md`, and
   whether every MCP tool is named in `src/mcp_server/CLAUDE.md`. It also reports which
   `CLAUDE.md` files were last committed before the code beside them — that one is advisory, since
   a commit that touches code need not touch its document, while the rest fail.

   It also refuses a `CLAUDE.md` that names a `src/`, `root/` or `tests/` path which does not
   exist, because such a file is read as fact and the next session imports from it. **The project
   root `CLAUDE.md` is exempt**, and only that one: it states where code goes rather than what is
   there, so `src/common/exceptions.py` in it is a destination, not a claim. Every file below the
   root describes its own directory, and there the same string is a claim.

   The staleness check needs git history and says so when there is none. Everything else works in
   a checkout that is not a repository.

2. Fix what it reports, then run it again until it is silent.
3. Every entry carries a short note saying **why the file exists** — not what its name already says.
   A tree without notes is `ls` with extra steps.

   ```
   ├── selectors.py
   ├── selectors.py             read queries, scope enforced here
   ```

4. Keep the notes in English, and **one line per entry**. A note that needs a second line is too
   long — shorten it, or move the detail to the app's `CLAUDE.md`.
5. Order is exactly `LC_ALL=C sort` on the entry names inside each directory, which is the order
   `find . | sort` prints. Directories are not grouped ahead of files; `migrations/` would sit
   between `managers.py` and `models.py` because that is where the sort puts it. The checker
   enforces this, so a diff only ever shows what really changed.

## What is not listed

Generated and ignored paths are out of scope and must not appear:
`.venv/`, `.idea/`, `__pycache__/`, `.git/`, `.pytest_cache/`, `staticfiles/`, `media/`, `logs/`,
coverage and build output.

Two git-ignored paths **are** listed, because a reader of a working checkout needs to know they
exist: `.env` and `.claude/settings.local.json`. The checker carries the same two as an explicit
allowlist — anything else that git ignores is invisible to it.

## What to pay attention to

- **A file with no reason to exist is deleted, not documented.** If writing the note is hard
  because the file has no clear job, that is the finding — remove it or merge it.
- **A file in the wrong place is moved, not explained.** The note must not read
  "temporary, belongs in services". Move it.
- **Empty placeholder files are not created.** No `utils.py` waiting to be filled — that is YAGNI.
- **A new top-level directory is a decision**, not a detail. State what it is for and why nothing
  existing could hold it, in `docs/structure-decisions.md`.
- If two directories would need the same note, one of them is redundant.

## Current tree

```
instagram-mcpserver/
├── .claude/
│   ├── rules -> ../docs/rules  symlink; how Claude Code discovers the rules
│   └── settings.local.json     local Claude Code settings and hooks, not shared
├── .env                        local secrets, git-ignored
├── .env.example                the same keys with empty values, committed
├── .gitignore                  secrets, generated output, IDE files; .claude/ stays tracked
├── CLAUDE.md                   project entrypoint, loaded every session
├── Makefile                    the commands, and `make check` — the gate before a commit
├── docs/
│   ├── api/
│   │   └── README.md           the error contract, the map, and where to start
│   ├── rules/
│   │   ├── README.md           index — which rule loads when, and what is deliberately absent
│   │   ├── api-docs.md         how to write the API .md handed to a caller
│   │   ├── api-drf.md          REST: no versions, errors, pagination, what DRF already does
│   │   ├── claude-md.md        how to write and maintain CLAUDE.md files
│   │   ├── core.md             style, naming, imports, SOLID, KISS, YAGNI, OOP and MRO
│   │   ├── dependencies.md     uv, no hand-written versions, runtime or dev
│   │   ├── django.md           models, migrations, ORM, the pool, settings
│   │   ├── git.md              commit authorship and messages, what never gets committed
│   │   ├── instagram.md        the Graph API: versions, tokens, quotas, webhooks, errors
│   │   ├── integrations.md     outbound clients, retry, circuit breaker, webhooks
│   │   ├── mcp.md              MCP tools, scopes, what is never exposed, data safety
│   │   ├── reporting.md        how short the answer after finished work has to be
│   │   ├── security.md         tokens, secrets, permissions, hostile text, rate limits
│   │   ├── services.md         services and selectors, and why both surfaces share them
│   │   ├── structure.md        this file
│   │   └── testing.md          pytest, what every endpoint and every tool must cover
│   └── structure-decisions.md  running log of structure decisions, and what is still open
├── manage.py                   Django CLI
├── pyproject.toml              project metadata, dependencies and pytest configuration
├── root/
│   ├── CLAUDE.md               configuration: env layering, what is absent and why
│   ├── __init__.py             package marker
│   ├── asgi.py                 the ASGI entrypoint; there is no WSGI one
│   ├── conf.py                 reads .env through pydantic-settings; only settings.py imports it
│   ├── settings.py             JSON-only Django config, PostgreSQL, no admin, no static
│   └── urls.py                 the generated schema and Swagger UI
├── scripts/
│   ├── check-docs.sh           what `make check` runs last: the tree, the claims, the map
│   ├── claude-hook.sh          Claude Code hooks — nudge on a stale CLAUDE.md, gate on a red check
│   └── clean-pycache.sh        remove every __pycache__ outside .venv
├── src/
│   └── __init__.py             package marker; every app will live under this name
└── tests/
    ├── CLAUDE.md               the suite: what is pinned, what must be running
    ├── __init__.py             package marker
    └── root/
        ├── __init__.py         package marker
        ├── test_conf.py        the secret refuses to be empty, short, defaulted or printed
        ├── test_settings.py    what must stay out of INSTALLED_APPS, MIDDLEWARE and TEMPLATES
        └── test_urls.py        the schema and Swagger UI answer, and no path is slash-redirected
└── uv.lock                     the resolved versions; the only thing that pins one
```
