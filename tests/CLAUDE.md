# tests

`pytest` + `pytest-django`. Configuration is in `pyproject.toml` under
`[tool.pytest.ini_options]`.

One file for the whole suite, not one per app: business rules live in `src/<app>/CLAUDE.md`, and a
second copy would drift from the first.

## Running

```
uv run pytest
uv run pytest tests/root
uv run pytest -k secret
```

No test touches the database yet, so the suite is offline and takes well under a second.

**The first one that does needs PostgreSQL running.** `pytest-django` creates and drops
`test_<POSTGRES_DB>`, so the role in `.env` needs `CREATEDB`:

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
└── root/                   environment parsing, the settings that must stay absent, the two schema paths
```

No `conftest.py` yet. It arrives with the first fixture two files share.

## What is pinned here

- **`SECRET_KEY` refuses to be empty or short.** A required `SecretStr` alone is not enough:
  `SECRET_KEY=` in the environment satisfies "required" with an empty string. The length floor in
  `root/conf.py` is what makes it fail closed, and the parametrized test is what keeps the floor
  from being dropped as an inconvenience.
- **Every required key is missing rather than defaulted.** The test is parametrized over the set,
  so a key added to `Env` with a convenient default fails here instead of shipping — which is the
  whole mechanism behind "no secret in code".
- **No secret appears in `repr(env)`.** That is the property keeping it out of a traceback, and it
  is `SecretStr`'s rather than our discipline — so it is tested, not assumed.
- **What must stay out of `INSTALLED_APPS`** — admin, sessions, staticfiles. Each was removed for a
  stated reason in `root/CLAUDE.md`, and each is the kind of line a future `startapp` or a
  copy-pasted settings block puts back.
- **`CommonMiddleware` stays out**, and a slashless path answers `404` rather than a redirect. That
  is the observable half of the same decision: `APPEND_SLASH` answers a slashless `POST` with a
  `301` that drops the body.
- **`TEMPLATES` stays empty of everything but `APP_DIRS`.** It exists for `drf-spectacular` and
  nothing else, and the test is what says so to whoever wants to add a `DIRS` entry.
- **JSON is the only renderer and parser**, so DRF cannot render its browsable HTML page at all.
- **The generated schema and Swagger UI answer.** Cheap, and it catches a settings change that
  breaks the one surface a caller has today.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file when a fixture, a factory or a dependency of the suite changes.
