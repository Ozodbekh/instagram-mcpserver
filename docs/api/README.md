# API documentation

What a caller of this API reads. One file per app: `docs/api/<app>.md`.

The OpenAPI schema at `/api/schema/` is the machine contract and is generated — never hand-written.
These files are the human contract: what an endpoint means, which order calls go in, and what an
error code implies. **An endpoint is not finished until its file here is updated in the same
change**, and a new page is not finished until a row below names it.

Every path is relative to `/api/`. **There is no version segment** — this API is not versioned, and
`docs/rules/api-drf.md` says why.

## Errors

Every error response is a machine-readable code. Never a sentence — the UI maps codes to messages
itself.

```json
{"code": "permission_denied"}
```

```json
{"code": "validation_error", "errors": {"caption": ["max_length"], "media_url": ["required"]}}
```

The entries under `errors` are codes too: `required`, `invalid`, `blank`, `max_length`.

### Codes every endpoint may return

| Status | `code` | Meaning |
|---|---|---|
| `400` | `validation_error` | The body failed validation. `errors` names the fields. |
| `400` | `bad_request` | The request could not be parsed. |
| `401` | `not_authenticated` | No token, an expired token or a wrong one — deliberately indistinguishable. |
| `403` | `permission_denied` | Authenticated, but not allowed. |
| `404` | `not_found` | No such object, or not one this account may see. |
| `405` | `method_not_allowed` | Wrong HTTP method for the path. |
| `409` | `conflict` | The action collides with something that already exists. |
| `415` | `unsupported_media_type` | Wrong `Content-Type`. |
| `429` | `throttled` | Rate limited by us. `Retry-After` says for how long. |

Anything beyond this list is specific to one endpoint and is documented on that endpoint.

**Renaming a code is a breaking change.**

### Codes that mean Meta, not us

A Graph API failure is translated at the integration boundary and never forwarded — Meta's own
message is written for our developers, is localized, and changes without notice. These are the
families a caller has to handle differently:

| Status | `code` | What the caller should do |
|---|---|---|
| `409` | `account_disconnected` | The account's token no longer works. A person must reconnect it. |
| `409` | `publishing_limit_reached` | The account's rolling publishing quota is spent. Wait for the window. |
| `429` | `upstream_throttled` | Meta's rate limit, not ours. Back off; retrying sooner spends the quota that would have recovered. |
| `502` | `upstream_unavailable` | Meta refused or did not answer. Transient — retry with backoff. |
| `502` | `upstream_error` | Anything else Meta returned. Not retryable without a change. |

## What is eventually consistent

Reads at Meta lag writes. A post published a moment ago may not appear in a media list, and
insights arrive late and get restated. That is Meta's timing, not a defect here. Any endpoint that
answers from our stored copy rather than a live read says so on its own page, and says how stale
it can be.

## Where a path lives

**A path does not name the app that serves it.** Each app declares its own url segment, so find
the page here first and then read it.

| Path | Page |
|---|---|
| — | no product endpoint exists yet |

`/api/schema/` and `/api/docs/` are the generated schema and Swagger UI. They are not product
endpoints and have no page, and **they are served only when `DEBUG` is on** — in any deployed
environment both answer `404`. Read the schema from a development instance, or generate it with
`manage.py spectacular`.

## Where to start

Nothing to call yet. The first app to land adds its row above and its page beside this file.
