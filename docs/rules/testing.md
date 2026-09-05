---
paths:
  - "tests/**"
  - "**/conftest.py"
---

# Testing

`pytest` + `pytest-django`. Run with `uv run pytest`.

**Tests are not optional here.** Every rule in this repository is a claim about behaviour, and a
claim nothing checks is a claim that has already drifted. An endpoint, a service, a tool or a
constraint without tests is unfinished work, not work with a follow-up.

Tests hit the JSON API with DRF's `APIClient`. Never `django.test.Client` against a template view,
never pytest-django's `admin_client` — this project has no Django admin and no templates.

## Layout

All tests live in the central `tests/` package, never inside an app. `tests/` mirrors `src/` and
`root/` exactly.

```
tests/
├── conftest.py
├── common/
├── integrations/          the Graph API client, the SDK mocked
├── mcp_server/            the bearer, the token endpoint and every tool
└── root/                  environment parsing
```

There are no version directories, because the API has no versions — `api-drf.md`.

`tests/CLAUDE.md` is the only one in the tree. It holds what is true of the suite itself —
fixtures, what must be running, what is mocked — never the business rules, which already live in
`src/<app>/CLAUDE.md`.

## Fixtures

- A factory produces a valid minimal object; tests override only the fields they care about.
- No shared mutable state, and no fixture that depends on execution order.
- Database access is explicit: `db` or `@pytest.mark.django_db`.
- **A test that reads a token from a fixture uses a fake one that could never work.** Never a real
  token, not even an expired one — an expired token is a rotated token that somebody forgot to
  rotate.

## What every endpoint must cover

1. **Happy path** — correct input, expected status and payload shape.
2. **Validation error** — a missing or malformed field, with the right field codes.
3. **Unauthenticated** — `401`.
4. **Forbidden** — an authenticated user without the permission or the scope, and proof they
   cannot read or change another user's data.

Anything less is an untested endpoint.

## What every MCP tool must cover

1. **Allowed scope** — the tool answers.
2. **Missing scope** — it refuses with the code, and refuses *inside the tool*, not only at connect.
3. **Truncation** — an oversized result is bounded and says it was bounded.
4. **No credential in the result** — assert the token is absent from the payload, by value.
5. **Untrusted text is delimited** — a caption containing an instruction comes back delimited and
   capped, not inlined.

## What else must be covered

- **Services** without HTTP and without MCP: call the function, assert the database state and the
  raised codes.
- **Selectors** for scope: a user must not see rows belonging to someone else.
- **State transitions** on the illegal path too — publishing an already-published container,
  refreshing a token on a disconnected account.
- **Constraints** — a `UniqueConstraint` or `CheckConstraint` is proven by a test that violates it.
- **N+1** — list endpoints assert a query count with `django_assert_num_queries`.
- **Webhooks** — valid signature, invalid signature, wrong verify token, replayed event, unknown
  event type, and an empty configured secret refusing everything.
- **Graph API error mapping** — one test per error family, from a real payload shape, asserting our
  code and that Meta's message did not reach the caller.
- **Idempotency** — the retry that must not produce a second post, run twice.

## What is mocked

- **Every outbound call. Tests never reach Meta**, and never reach the internet. A test that would
  need a real token is a test that must be rewritten, not skipped.
- Time is frozen where behaviour depends on it — token expiry windows, quota windows. Never `sleep`.
- Background work runs eagerly, or the enqueue is asserted. Never both silently.

## Style

- One behaviour per test, and the name states it: `test_media_publish_rejects_used_container`.
- Arrange, act, assert — in that order, no interleaving.
- Assert on the specific code and field, not on a whole response body, unless the body **is** the
  contract being pinned.
- No `if` and no loops over cases; use `@pytest.mark.parametrize`.
- No comments, exactly as in production code.

## Definition of done

1. New endpoint: the four cases above exist and pass.
2. New tool: the five cases above exist and pass.
3. New service: its rules and its failure modes are tested without HTTP.
4. New model constraint: a test proves the database rejects the violation.
5. `uv run pytest` passes and `makemigrations --check --dry-run` reports nothing missing.
