# Structure decisions

Running notes for the file-structure discussion. Every decision agreed in conversation is
written here as it is made, before any directory is created.

This is a working log, not the map. The map is `docs/rules/structure.md` and it only ever shows
what already exists. When something here is built, it moves there.

It is also the **only** document allowed to describe what does not exist yet. A `CLAUDE.md` is read
as fact, so a plan written in one gets imported from — `docs/rules/claude-md.md`.

---

## Agreed

### No API versions, and no sides

**Decided.** There is no `v1/`, no `shared/`, and no `front_office` / `back_office` split. An app is
`src/<name>/` and its endpoints live in it, flat.

A version directory buys the ability to change a contract without breaking a client that cannot be
updated. The consumers here are the MCP server in this repository and whatever calls the HTTP API,
and both ship when we say so. Building the level now means a directory that never holds a second
entry, and a `tests/` mirror that copies it.

If a breaking change ever has to ship beside the old shape, the version arrives then — and this
file gains the entry saying why.

The rules were ported from a project that has both, and every trace of them was removed rather
than kept "in case": `docs/api/` is flat, `claude-md.md` has three levels instead of five, and
`check-docs.sh` has no side segment.

### `root/urls.py` reaches `src/` once and stops

Today it routes the generated schema and Swagger UI and nothing else.

When the first app lands, it gains one `include` of a single collector under `src/`, and that
collector names the apps. No app's own url module carries the `api/` prefix, so changing the prefix
stays a one-line edit and adding an app never touches `root/`.

### The MCP server is `src/mcp_server/`, in its own process

Never `src/mcp/` — a top-level `mcp/` package shadows the installed `mcp` SDK that `fastmcp` is
built on, and the failure is an import error a long way from the cause.

It is a Django app (`INSTALLED_APPS`, so the ORM and migrations work) but it does not serve HTTP
through Django. `main.py` calls `django.setup()` and builds its own Starlette app around FastMCP's
Streamable HTTP transport, started separately from the API.

Two surfaces, one set of services. The rule that keeps them honest is in `docs/rules/services.md`:
a tool calls the same `selectors.py` a view does, so a row an agent must not see is unreachable
rather than merely unrequested.

### Everything outbound is `src/integrations/instagram/`

Not a Django app: no models, no migrations, not installed. It carries a call out and decides
nothing.

The consequence that matters is that the client stores nothing. A token belongs to a domain app's
model, because a client that keeps its own copy becomes the second place tokens live, and the two
diverge on the first refresh.

Which of Meta's two Instagram APIs this project uses — Instagram Login or Facebook Login — is
**not yet decided**. It is the first thing to settle, it changes permission names, id spaces and
endpoints, and `src/integrations/instagram/CLAUDE.md` records the answer on the day the directory
is created.

### PostgreSQL, pooled, `CONN_MAX_AGE = 0`

**Decided.** SQLite was the scaffold's default and lasted until the first real decision.

The trigger is concrete: a background worker writing synced rows while the API reads them, and the
MCP server reading them from a third process. SQLite has one writer, so that is `database is
locked` under any real concurrency — and the sync is the first thing that will run concurrently.

`CONN_MAX_AGE` and `pool` are mutually exclusive in Django, and the pool is the right half of the
choice. A persistent connection is recycled at a request boundary, and **the MCP server has no
request boundary**: it is a long-lived async process reaching the ORM through `sync_to_async`, so a
connection opened there is pinned to a thread and never released. The pool solves reuse per
process instead of per thread, which is the shape this project actually has.

The pool runs on psycopg's defaults. Sizing is configuration the day something measures it, and a
number guessed before then is a number nobody can defend — `docs/rules/django.md` says what
changes when it is.

---

## Open

### Background work

There is none, and Celery is not installed. That is a gap, not a decision — three things this
project needs are background work by nature:

- **Token refresh**, on a schedule, before expiry rather than after a failure.
- **Publishing**, which is create-a-container, poll it, publish it — never inside a request.
- **Syncing** media and insights, page by page, inside Meta's rate limits.

The choice is Celery with a broker versus a management command run from cron versus something
smaller. It is deliberately not made yet: the first of the three to be built decides it, and this
entry is replaced by what it chose. Until then `docs/rules/README.md` carries no `celery.md`,
because a rule for machinery nobody runs reads as fact.

### Where a token lives

Agreed that it belongs to a domain app's model and never to the integration package. Not yet
agreed: encrypted at rest or not, and with which key.

`docs/rules/security.md` requires one or the other — encryption, or an entry in
`docs/security-debt.md` saying it is absent and what would add it. The app that first stores a
token writes whichever is true.

### `src/common/`

Does not exist. It arrives with the **second** app that needs a shared piece, not the first —
`docs/rules/core.md`, DRY against YAGNI. What it is expected to hold when it does: `models.py`
(`TimeStampedModel`, `UUIDModel`, `SoftDeleteMixin`), `exceptions.py` (the DRF exception handler),
`pagination.py`, `scope.py`, `constants.py`.

Naming it now would be a directory with one file in it, imported from one place.
