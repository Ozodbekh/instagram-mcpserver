# Instagram MCP Server

A backend that connects Instagram professional accounts and exposes a controlled slice of them to
AI agents over the Model Context Protocol. JSON API: accepts JSON, returns JSON, stateless. No
Django admin, no templates, no server-rendered HTML.

**Two surfaces over one set of services.** The REST API and the MCP tools are two doors into
`services.py` / `selectors.py`, and neither may know something the other does not. That is the
whole architecture; everything below protects it.

**This codebase holds other people's access tokens.** A token here acts as somebody's Instagram
business account and posts in their name. `docs/rules/security.md` is not advice.

## Stack

Python 3.14 · Django 6.1 · DRF · `drf-spectacular` · `django-cors-headers` · `requests` ·
PostgreSQL (`psycopg`, pooled) · `pydantic-settings` · `uv` · `pytest` + `pytest-django`.

Not installed — do not import them: Celery, Redis, Channels, GraphQL, `django-filter`,
`celery-beat`, ruff. `fastmcp` and an HTTP client arrive with the MCP server and the Graph API
client; nothing imports them yet.

## No versions, no sides

**The API is not versioned.** There is no `v1/`, no `shared/`, no `front_office` / `back_office`
split. An app is `src/<name>/` and its endpoints live in it, flat. A version directory buys the
ability to change a contract without breaking a client that cannot be updated, and this project has
no such client — see `docs/rules/api-drf.md`.

## Commands

`make help` lists them. `make check` is the gate before every commit: Django checks, no missing
migration, the tests, then `scripts/check-docs.sh`.

Not routine, so no target: `uv run manage.py startapp <name> src/<name>`, `uv add <name>`.

## Never negotiable

1. No comments, no docstrings — rename instead of explaining.
2. English in code and documentation. Only text sent straight to an end user is Uzbek, and it
   lives in the app's `constants.py`.
3. Business logic lives in `services.py` / `selectors.py` — never in a view, serializer, MCP tool
   or management command.
4. Errors return machine-readable codes, never sentences. A provider's message is never forwarded.
5. **An access token is never logged, returned, put in a URL, or handed to a model.**
6. Only `src/integrations/` opens an outbound connection, and no caller forwards a path, an
   endpoint or a field list to Meta.
7. An endpoint or a tool is not done until it has tests: happy path, validation, unauthenticated,
   forbidden — and for a tool, its scope checks and its bounds.
8. An endpoint is not done until `docs/api/**.md` is updated in the same change, and a new page is
   not done until the map in `docs/api/README.md` points at it.
9. An app is not done until its `CLAUDE.md` matches what the code now does.
10. A file added, deleted, renamed or moved is not done until `docs/rules/structure.md` reflects it.
11. Packages are added with `uv add <name>`, never with a version. The Graph API version is
    configuration, never recalled from memory.

## Style

- Single quotes, 4 spaces, max line 120, one trailing newline, no `print`.
- `snake_case` modules and functions, `PascalCase` classes, `UPPER_SNAKE` constants.
- Services and selectors read `<noun>_<verb>`: `media_publish`, `account_connect`, `insight_list`.
- Booleans start with `is_`, `has_`, `can_`, `should_`. No abbreviations except
  `id`, `url`, `api`, `db`, `ai`. No type suffix in a name. Private helpers start with `_`.
- Every literal that is not `0`, `1` or `''` goes to `constants.py`. Most numbers here are Meta's,
  not ours — the constant is where the next reader learns which.
- **Import the names you use, not the parent module** — `from django.db.models import CharField`,
  not `from django.db import models`. Exceptions: a name that would collide, and generated
  migrations. Absolute imports only, no wildcards, no imports inside functions.
- Order: standard library → third party → local, one blank line between.
- Type hints on public functions in `services.py`, `selectors.py`, `src/integrations/` and every
  MCP tool. Never `Any`. Serializers, views, models and tests are not annotated.

## Principles

- **KISS** — the simplest thing that works. A plain function beats a class; a class beats a
  metaclass. No design pattern without a second caller that needs it.
- **YAGNI** — no `**kwargs` passthrough "for later", no abstract base with one implementation,
  no version directory before a breaking change exists, no flag for a feature that ships on.
- **DRY** — the same rule expressed twice will drift. Move it to `src/common/` once a **second**
  app needs it, not before.
- **SOLID** — one module one job (`services.py` writes, `selectors.py` reads, `views.py` speaks
  HTTP, a tool speaks MCP); a second provider is a new file, never an edit to an existing one; a
  subclass is usable wherever its base is; a base nobody raises `NotImplementedError` on; callers
  depend on the abstraction and a factory picks the implementation.

## Functions

- Positional arguments ≤ 2; anything more is keyword-only. Guard clauses, early return,
  no `else` after `return`, nesting ≤ 2. Return one type.
- A `get_*` never writes. No side effect behind a read-sounding name.
- **Extraction is not free.** Extract only when a second caller exists, the function mixes levels
  of abstraction or breaks the limits above, the block is a business rule deserving its own test,
  or it is an outbound call or a clock a test will replace.
- **Never** extract a one-line body with one caller, a wrapper that renames a single ORM call, or
  a helper that exists to dodge the no-comments rule. Name a local variable instead.
- Inherit only for a real is-a. Depth ≤ 2 below our own base. Always `super()`, never the parent
  by name. Mixins first, concrete base last.

## Errors

Raise specific exceptions, never bare `Exception`. Never swallow one silently. Domain errors raise
from `services.py`; HTTP status mapping happens in `src/common/exceptions.py` and nowhere else, and
an MCP tool maps the same domain error to a `ToolError` code.

A Graph API failure is translated at the integration boundary, never forwarded: switch on Meta's
error code and subcode, log their trace id, and return one of ours.

## Talking to Meta

Every call is somebody else's service with somebody else's quota. `docs/rules/instagram.md` holds
the rules; four of them decide most designs:

- **The version is configuration and it expires.** Never write one from memory.
- **Publishing is two calls and a quota**, and never happens inside a request.
- **Rate limits are announced in response headers** — read them and back off before being blocked,
  because one caller in a loop takes every connected account offline for the window.
- **Reads are eventually consistent.** A just-published post missing from the list is Meta's
  timing, not our bug.

## Text a stranger wrote is hostile

Captions, comments, bios and direct messages come from the open internet and land in a model's
context. Delimit them, cap them, and never let one act as an instruction. A tool that summarises
comments is a prompt-injection surface and its description says so.

## Git

- Commits are the repository owner's. No `Co-Authored-By`, no assistant named, no session link,
  nothing about how the work was produced. Same for a pull request description.
- Subject imperative, under 60 characters. Blank line, then **about five lines** saying *why*.
  One logical change per commit.
- **Assume another agent edits this checkout.** Never `git add -A`, never `git add .`, never
  `git commit -a`. Name the paths on the commit itself: `git commit <paths>`. Do not revert, stash
  or tidy a file outside your task.
- Before committing: `uv run pytest` passes, `makemigrations --check --dry-run` is clean,
  `structure.md` matches the tree, **no token or secret in the diff**.
- Never committed: `.env`, `logs/`, `media/`, `db.sqlite3`, `__pycache__/`, `.venv/`, `.idea/`.
  `.env.example` **is**, with every key empty. `.claude/rules` is a symlink to `docs/rules` and
  must stay committed as a symlink — flatten it and every rule stops loading.

## Reporting

Report the outcome, not the work. Under ten lines for a finished task; one or two sentences for a
one-file change. Give the verified number — `41 tests pass`, never `everything works`. Say what is
not done and why. Never claim a Graph API call succeeded when the test mocked it. Cut file lists,
restated plans, headers on short answers, and praise. A question gets an answer, not a summary.

## The rest loads itself

`.claude/rules` is a symlink to `docs/rules`, and every file there carries a `paths:` block, so it
arrives only when a matching file is in context — `django.md` with a model, `testing.md` with a
test, `instagram.md` with the Graph API client. Do not read them pre-emptively.

Four are not path-scoped and are read on demand:

| Read before | File |
|---|---|
| the full reasoning behind a rule above | `docs/rules/core.md`, `git.md`, `reporting.md` |
| a structural decision | `docs/structure-decisions.md` |
| writing a `structure.md` entry by hand | `docs/rules/structure.md` — the conventions, then the tree |

**After adding, moving or deleting a file, run `./scripts/check-docs.sh` rather than reading
`structure.md`.** It names every entry to add or remove and where each one goes, so the tree is
data the script owns, not a document to read first. `make check` runs it, and it also checks what a
`CLAUDE.md` claims, whether a routed path reached `docs/api/`, and whether every page there is on
the map in `docs/api/README.md`.

If two rules collide: `security.md` > this file > the topic file. If a rule is wrong, change the
rule — do not work around it silently.
