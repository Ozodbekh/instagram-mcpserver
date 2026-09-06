# tests

`pytest` + `pytest-django`. Configuration is in `pyproject.toml` under
`[tool.pytest.ini_options]`.

One file for the whole suite, not one per app: business rules live in `src/<app>/CLAUDE.md`, and a
second copy would drift from the first.

## Running

```
uv run pytest
uv run pytest tests/webhooks
uv run pytest -k signature
uv run pytest tests/root tests/common tests/integrations   everything that needs no database
```

**Nothing has to be running.** No test touches the database, because nothing under `src/` has a
model — the whole suite is offline and finishes in well under a second.

The first test that does need one will need PostgreSQL up, and the role in `.env` will need
`CREATEDB`, because `pytest-django` creates and drops `test_<POSTGRES_DB>`:

```
sudo -u postgres psql -c "ALTER USER <POSTGRES_USER> CREATEDB;"
```

Without it every test errors at setup, including the ones that never touch the database — the
session-scoped database fixture fails first and the failure cascades.

## Layout

`tests/` mirrors the tree it exercises, `root/` included. There are no version directories, because
the API has no versions — `docs/rules/api-drf.md`.

```
tests/
├── common/                 the error envelope, exception by exception
├── integrations/telegram/  the Bot API client, requests mocked
├── root/                   environment parsing, the settings that must stay absent, CORS, the schema paths
└── webhooks/               Meta's two calls: verification, signature, replay, forwarding
```

No root `conftest.py` yet. `tests/webhooks/conftest.py` holds the signed-payload builder and two
autouse fixtures: one sets the app secret, verify token and Telegram configuration, the other
patches `message_send` so **no test can reach the network even by mistake**.

## What is pinned here

- **`SECRET_KEY` refuses to be empty or short.** A required `SecretStr` alone is not enough:
  `SECRET_KEY=` in the environment satisfies "required" with an empty string. The length floor in
  `root/conf.py` is what makes it fail closed.
- **Every required key is missing rather than defaulted.** The test is parametrized over the set,
  so a key added to `Env` with a convenient default fails here instead of shipping.
- **No secret appears in `repr(env)`.** That is `SecretStr`'s property rather than our discipline —
  so it is tested, not assumed.
- **What must stay out of `INSTALLED_APPS`** — admin, sessions, staticfiles — and that
  `CommonMiddleware` stays out, so a slashless path answers `404` rather than a body-dropping
  redirect.
- **DRF fails closed.** `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated` and
  `DEFAULT_AUTHENTICATION_CLASSES` is empty, asserted against `api_settings` rather than our own
  dict. `BasicAuthentication` is named explicitly: it is the one DRF enables by default and the one
  that would accept a password on every view.
- **CORS, including a real preflight**, and `authorization` beside the `*` in `CORS_ALLOW_HEADERS` —
  the Fetch specification excludes `Authorization` from the wildcard, and that failure appears only
  in a browser.
- **The schema and Swagger UI exist only under `DEBUG`**, tested by reloading the URL conf under
  each flag. A permission cannot express this — `drf-spectacular` serves them with its own
  `AllowAny`.
- **The webhook signature covers bytes, not the parsed body.** One test signs a re-serialised copy
  of the same object and asserts the delivery is refused. That is the mistake the rule exists for,
  and every other test would pass with it made.
- **An empty app secret or verify token refuses everything**, rather than matching an empty one.
- **A redelivery is forwarded again.** The test asserts the duplicate rather than preventing it, so
  the absence of idempotency is a decision on record instead of an oversight — see
  `src/webhooks/CLAUDE.md`.
- **A Telegram failure still answers Meta `200`, and stops the rest of the delivery.** The first
  is so Meta does not redeliver what Telegram already refused; the second is so an unreachable
  Telegram costs one timeout inside Meta's request, not one per event.
- **`message_send` never sends `parse_mode`.** The text is a stranger's comment; a formatting flag
  turns it into markup somebody else chose.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file when a fixture, a factory or a dependency of the suite changes.
