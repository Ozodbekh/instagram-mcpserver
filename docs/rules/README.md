---
paths:
  - "docs/rules/README.md"
---

# Rules

Coding rules for the Instagram MCP server. Every AI and developer follows them.

They live in `docs/rules/` so they are visible on GitHub and reviewed like any other document.
`.claude/rules` is a symlink to this directory — that is how Claude Code finds them, and it must
stay committed as a symlink.

## How they load

**Every file here carries a `paths:` frontmatter block, so none of them is in context by default.**
A file arrives when a path it names is read. Nothing is loaded pre-emptively, and nothing has to be
loaded by hand for the common case.

The rules that apply to *every* line of work are not here at all — they are in the root
`CLAUDE.md`, which is the only document loaded at startup. This file and the four below hold the
full reasoning behind them; the root file holds the rules themselves.

| File | Arrives with |
|---|---|
| `django.md` | models, managers, apps, migrations, settings |
| `services.md` | `services.py`, `selectors.py`, `tasks.py`, `signals.py` |
| `api-drf.md` | serializers, views, urls, filters, permissions |
| `api-docs.md` | views, urls, serializers, and `docs/api/**` |
| `security.md` | any file under `src/`, and settings |
| `testing.md` | anything under `tests/`, and every `conftest.py` |
| `mcp.md` | `src/mcp_server/**` |
| `instagram.md` | `src/integrations/instagram/**`, any `webhooks.py` |
| `integrations.md` | `src/integrations/**` |
| `dependencies.md` | `pyproject.toml`, `uv.lock` |
| `claude-md.md` | any `CLAUDE.md` |

Four carry no trigger of their own and are read deliberately, by opening them:

| File | Read it when |
|---|---|
| `structure.md` | adding, moving, renaming or deleting any file |
| `core.md` | the reasoning behind a style or extraction rule is in question |
| `git.md` | the reasoning behind a commit or authorship rule is in question |
| `reporting.md` | the reasoning behind how short an answer must be is in question |

Their rules are already in the root `CLAUDE.md` in one-line form. These files exist so a rule can be
argued with rather than merely obeyed — and so nothing was lost when the short form was written.

## What is deliberately not here

A rule for machinery this project does not run is dead weight that reads as fact. There is no
`celery.md`, no `cache.md`, no `websocket.md`, no `graphql.md`, no `logging.md` — Celery, Redis,
Channels, GraphQL and a custom logging package are not installed, and a rule describing how to use
one of them would have the next reader importing it.

The one logging rule that holds regardless — standard library, `getLogger(__name__)`, structured
`extra`, no `print`, no token — is in `security.md`.

**When one of those arrives, its rule file arrives in the same change**, and this table gains a
row. Not before, and not after.

## Conflicts

`security.md` > root `CLAUDE.md` > the topic file. If a rule is wrong, change the rule — do not
work around it silently.

## The non-negotiables

They are in the root `CLAUDE.md`, once. Two copies of a rule drift apart — which is the failure
`claude-md.md` warns about.
