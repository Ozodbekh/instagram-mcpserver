---
paths:
  - "src/**/models.py"
  - "src/**/managers.py"
  - "src/**/apps.py"
  - "src/**/migrations/**"
  - "root/settings.py"
  - "root/conf.py"
---

# Django

Django 6.1, Python 3.14, PostgreSQL via `psycopg` 3.

## JSON in, JSON out

No Django admin, no template rendering, no forms, no server-side HTML, no sessions, no
cookie login.

- No `admin.py` anywhere. `startapp` generates one — delete it with the generated `tests.py`.
  Never register a model, never add `django.contrib.admin`.
- Never write a template, a `DIRS` entry, a context processor or a `render()` call. The `TEMPLATES`
  block exists **only** so third-party packages can serve their own pages — today that is
  `drf-spectacular`'s Swagger UI. That is why `APP_DIRS = True` and `DIRS` and `context_processors`
  are empty. Leave it alone.
- `MIDDLEWARE` holds `SecurityMiddleware` and nothing else. `CommonMiddleware` is absent on
  purpose: `APPEND_SLASH` answers a slashless `POST` with a `301` that drops the body, and under
  `DEBUG` it raises instead. A JSON API wants a clean `404`.

## Apps

- An app lives at `src/<name>/`. There is no side directory and no version directory — see
  `api-drf.md`.
- Scaffold with `uv run manage.py startapp <name> src/<name>` — never hand-write the files.
- `name` in `apps.py` is the full dotted path (`src.accounts`), registered as that same path in
  `INSTALLED_APPS`. Declare `label` too, though Django would derive it.
- Choice enums go in `constants.py`, not `models.py`: `managers.py` needs them and `models.py`
  imports the manager, so defining them beside the model closes an import cycle.
- Create a `CLAUDE.md` beside the app. See `claude-md.md`.

## Models

`models.py` holds fields and `Meta` only. No business logic, no queries, no HTTP awareness, no
Graph API awareness.

- Inherit the shared bases from `src/common/models.py` — `TimeStampedModel`, `UUIDModel`,
  `SoftDeleteMixin` — instead of redeclaring `created_at` / `updated_at`.
- An optional text field defaults to `''`. Use `null=True` only when the column must genuinely hold
  NULL — dates, foreign keys, numbers — **and for any optional field that is also `unique`**,
  because `''` is a value and a second empty row collides, while Postgres allows any number of
  NULLs.
- `related_name` is mandatory on every `ForeignKey`, `OneToOneField` and `ManyToManyField`.
- `on_delete` is deliberate: `CASCADE` for owned data, `PROTECT` for referenced records,
  `SET_NULL` for optional links.
- Choices are `TextChoices` / `IntegerChoices` with English values.
- **Every id that came from Meta is a string, never an integer.** Instagram ids, container ids and
  page ids are decimal strings that already exceed 64 bits in places, and Meta documents them as
  opaque. Store `CharField`, index it, and never do arithmetic on one.
- **Meta's id is never our primary key.** It is a unique column beside our own key. An account can
  be reconnected, a media object re-fetched, and a foreign key pointing at somebody else's
  identifier makes every one of those a data migration.
- Money is `DecimalField(max_digits=..., decimal_places=2)`. Never `FloatField`.

### Options that must never appear in a model

They exist for Django forms and admin. This project has neither, so they do nothing except mislead
the next reader into thinking validation happens where it does not.

| Never | Why it does nothing here |
|---|---|
| `blank=True` | Only `ModelForm` reads it. DRF serializers own input validation. |
| `help_text=...` | Rendered by forms. The contract lives in `docs/api/`. |
| `verbose_name`, `Meta.verbose_name[_plural]` | Labels for a UI we do not render. |
| `error_messages=...` | Read by form validation, not by DRF. |
| `validators=[...]` on a field | Runs only in `full_clean()`, which nothing calls. |
| `unique_for_date` / `_month` / `_year` | `ModelForm` only — the database never learns about it. |
| `Model.clean()` / `full_clean()` | The form validation path. |

**A rule that must hold lives in two places:** the serializer, so the client gets
`validation_error`, and `Meta.constraints`, so it cannot be bypassed.

## Meta

Declare what the database must enforce — `ordering`, `indexes`, and `constraints` holding
`UniqueConstraint` and `CheckConstraint`.

- Every field used in a filter or ordering that is not already indexed gets an `Index`.
- Uniqueness is a database constraint, never a serializer check alone. `(account, instagram_id)`
  is the shape that stops a re-sync from doubling a row.
- **`db_table` is always declared**, even when it matches what Django derives. Without it the name
  is `<app_label>_<model>`, so moving a model to another app renames its table — a lock and a
  rewrite on anything large.
- **A constraint is a claim about the data that already exists.** Rows synced from Meta were
  written by a system that enforced none of ours, so count what would violate one before adding
  it. Either a data migration cleans those rows or the constraint does not go in.

## Managers and querysets

Reusable query fragments go in `managers.py` as `QuerySet` methods, not copied across selectors.
Managers expose queries; they never write.

## Migrations

- `make migrations`, **read the generated file**, then `make migrate`. Never chain the two:
  `makemigrations` can pick up a half-finished model change or prompt for a default, and applying
  it in the same breath removes the only moment you could have caught either.
- Rename the file to something meaningful: `0004_media_unique_per_account.py`.
- One migration per logical change. Never edit an applied migration — add a new one.
- Data migrations are separate from schema migrations, `RunPython` with a reverse function.
- `makemigrations --check --dry-run` must report no changes before work is done.

## Queries

- Every query touching a relation declares `select_related` (FK, O2O) or `prefetch_related`
  (M2M, reverse FK). N+1 is a bug, not a performance detail.
- `only()` / `defer()` / `values()` when the full row is not needed.
- Aggregate in the database (`Count`, `Sum`, `Exists`, `Subquery`), never in a Python loop.
- `count()` for counting, `exists()` for existence. Never `len(qs)` or `if qs:`.
- Bulk work uses `bulk_create` / `bulk_update` / `update()`, never a loop of `save()`. A sync that
  pulls a page of media writes it in one statement.
- Multi-statement writes are wrapped in `atomic`; deferred work runs in `on_commit`, never inside
  the transaction.

## Signals

**A signal triggers; a service does the work.** A receiver is a guard and a few calls, short enough
to read at a glance. The rule then stays testable without saving a model, and holds whichever path
wrote the row — a view, a command, the shell, an MCP tool.

- **The rule itself never lives in a receiver.** A branch, a calculation or a query belongs in
  `services.py`. Creating a row is not a rule — do not wrap `Model.objects.create(...)` in a
  service just to have something to call.
- **Take `update_fields` and use it.** A receiver that recomputes something expensive returns early
  when the save touched no field it depends on. `update_fields` is `None` on a plain `save()`,
  meaning "everything", so the guard narrows work and never narrows correctness.
- Receivers live in `signals.py` in the app owning the model, imported from `AppConfig.ready()` —
  inside `ready()`, with `# noqa: F401`, because it is imported for its side effect.
- **`dispatch_uid` on every receiver.** Without it a module imported twice connects twice and the
  handler runs twice, invisible until it is a duplicate row.
- A `post_save` receiver fires inside `save()`. If several must succeed together, the **caller**
  wraps the write in `atomic`.

### What signals do not see

`bulk_create`, `queryset.update()` and `queryset.delete()` do **not** fire per-row signals.

That matters here because a Graph API sync is written in bulk by design, so every receiver is
silent for exactly the rows that arrive in volume. An invariant that must hold for synced data is
checked by a query after the sync, not by a receiver.

`update()` also skips `auto_now`, so a service using it sets `updated_at` by hand.

## Database connections

`OPTIONS: {'pool': True}` — psycopg's own defaults. `ENGINE` stays
`django.db.backends.postgresql`; Django picks psycopg 3 when it is installed.

Sizing is not configured, because nothing has measured it yet. When it has to be, `True` becomes a
dict that Django passes straight to `psycopg_pool.ConnectionPool`, so every key must be one that
class accepts and every value must be the real object, not a dotted path.

### `CONN_MAX_AGE` is always 0

Not a workaround — the correct setting, and `CONN_MAX_AGE` and `pool` cannot both be active anyway.

A persistent connection is recycled at a request boundary, by `close_old_connections()` on
`request_started` / `request_finished`. **The MCP server has no request boundary.** It is a
long-lived async process that reaches the ORM through `sync_to_async`, so a connection opened there
is held in thread-local storage and never released: an idle connection gets dropped and the next
query raises `InterfaceError`, and every worker thread pins a connection until `max_connections`
runs out.

Avoiding a connection per request is the pool's job, and it does it **per process** rather than per
thread, so the problem does not recur.

Size it against the server when the time comes: the total is `max_size` × (API processes + the MCP
process + whatever runs the syncs), and that must stay under Postgres `max_connections`.

If stale connections ever appear, add `'check': ConnectionPool.check_connection` — it costs a round
trip per checkout, so add it on evidence, not by default.

## Settings

- `.env` is read by `root/conf.py`; `root/settings.py` imports `env` from there and is the only
  module allowed to. Nothing under `src/` may import either — application code reads
  `django.conf.settings`.
- Never hardcode a secret, host, key or URL. Add a field to `conf.py`, a key to `.env`, and the
  same key to `.env.example`.
- `USE_TZ = True`, store UTC. Meta returns timestamps with an offset; parse them, never
  reinterpret them.
- `AUTH_USER_MODEL` is set before the first migration if a custom user model is ever wanted. It
  can never be changed afterwards.
