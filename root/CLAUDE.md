# root

Django configuration. No application code lives here.

## Files

- `conf.py` — reads `.env` through `pydantic-settings` and exposes one `env` object.
- `settings.py` — the only module allowed to import `conf.py`.
- `asgi.py` — the ASGI entrypoint.
- `urls.py` — the schema and Swagger UI paths.
- `__init__.py`.

There is no `wsgi.py`. The MCP transport is Streamable HTTP and the server is async, so WSGI would
be a second entrypoint nothing starts.

## The one-way rule

`root/settings.py` imports `root/conf.py`. **Nothing under `src/` may import either.** Application
code reads `django.conf.settings`.

Import `conf` from `src/` and the dependency runs backwards, and `override_settings` stops working
in tests because the value was already captured at import time.

Adding a value: field on `Env` in `conf.py` → key in `.env` → key in `.env.example` → exposed
through `settings.py` if application code needs it.

## Secrets are typed

Every secret in `conf.py` is `SecretStr`. Printing one shows `**********`; the real value needs
`.get_secret_value()`, and only `settings.py` calls that. This is what keeps a secret out of a
traceback or a log line by construction rather than by discipline.

`SECRET_KEY` has **no default and a minimum length**, so a deployment without a `.env` refuses to
start instead of running on a value somebody committed — and an empty one is refused too. A
required field alone is not enough: `SECRET_KEY=` in the environment satisfies "required" with an
empty string, which is the same failure `docs/rules/security.md` describes for a webhook secret.
Every secret added here follows that shape: no default, and either a length floor or an explicit
emptiness check before it is compared.

## What is deliberately absent

- **`django.contrib.admin`, `sessions`, `messages`** — no admin, no session login, no cookie auth.
- **`django.contrib.staticfiles` and `STATIC_URL`** — nothing here serves static files. Swagger UI
  loads its assets from a CDN (`SWAGGER_UI_DIST = 'CDN'`), which is the only reason it is not
  needed.
- **`CommonMiddleware`** — its four jobs are `DISALLOWED_USER_AGENTS` (empty), `PREPEND_WWW`
  (off), `Content-Length` (the ASGI server sets it) and `APPEND_SLASH`. The last is actively wrong
  for a JSON API: a slashless `POST` gets a `301` that drops the body, and under `DEBUG` it raises
  instead. A clean `404` is the right answer.
- **`AUTH_PASSWORD_VALIDATORS`** — read by `validate_password()`, which only the form and admin
  paths call.
- **`LANGUAGE_CODE` and `USE_I18N`** — nothing is translated here; `USE_I18N = False`.
- **`MAILERS`** — no email is sent.
- **`wsgi.py` and `WSGI_APPLICATION`** — ASGI only.

`TEMPLATES` is present but empty of everything: no `DIRS`, no context processors. It exists so
`drf-spectacular` can render `/api/docs/`, and for nothing else. Do not add to it.

## Current state

- `INSTALLED_APPS`: Django's `auth` and `contenttypes`, then `rest_framework` and
  `drf_spectacular`. No app under `src/` exists yet.
- `MIDDLEWARE` holds `SecurityMiddleware` alone.
- PostgreSQL through `psycopg` 3, pooled, `CONN_MAX_AGE = 0` — the two are mutually exclusive, and
  the pool is the right half because the MCP server is a long-lived process with no request
  boundary at which Django would recycle a connection. See `docs/rules/django.md`.
  The pool runs on psycopg's own defaults (`'pool': True`) — nothing has measured it yet, and a
  size guessed now would be a number nobody could defend.
- `USE_TZ = True`, `TIME_ZONE = 'UTC'`. Meta returns offsets; parse them, never reinterpret them.
- `REST_FRAMEWORK` **overrides three DRF defaults that are open, and each override is the point**:
  `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`, so a view that forgets to declare one fails
  closed rather than serving everybody; `DEFAULT_AUTHENTICATION_CLASSES` is **empty**, because
  DRF's own default is `SessionAuthentication` + `BasicAuthentication` and the second would accept
  HTTP Basic against Django's auth backends on every view — an authentication mechanism nobody
  chose. JSON is the only renderer and the only parser, so `BrowsableAPIRenderer` cannot render its
  HTML page at all. `UNAUTHENTICATED_USER` is `None` because there is no `AuthenticationMiddleware`.
  The empty authentication list and that line are both revisited in the change that adds real
  authentication — `security.md` still requires every view to declare its own permissions.
- `SPECTACULAR_SETTINGS`: the schema is generated, never hand-written. `SERVE_INCLUDE_SCHEMA` is
  off so the schema endpoint does not describe itself.
- `urls.py` routes `/api/schema/` and `/api/docs/` **only when `DEBUG`**, and nothing else. No
  product path exists yet, so with `DEBUG` off the URL conf is empty and every path is `404`.
  The gate is on the route, not on a permission: `drf-spectacular` serves both views with
  `AllowAny` (`SERVE_PERMISSIONS`) whatever the DRF default is, so not routing them is the only
  thing that closes them.
- `conf.py` carries `SECRET_KEY` (`SecretStr`, at least 32 characters), `DEBUG`, `ALLOWED_HOSTS`
  (comma-separated, read through the `allowed_hosts` property), and the five `POSTGRES_*` keys.
  `POSTGRES_PASSWORD` is a `SecretStr` with no default, so the key must be present even when the
  value is empty for a locally trusted connection. Instagram credentials, the Graph API version and
  the MCP signing key are added when the code that reads them is written — not before.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file after changing configuration.
