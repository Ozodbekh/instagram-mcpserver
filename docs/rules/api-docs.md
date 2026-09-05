---
paths:
  - "src/**/views.py"
  - "src/**/urls.py"
  - "src/**/serializers.py"
  - "docs/api/**"
---

# API documentation

These files are the human-readable contract handed to whoever calls this API. They are written by
whoever writes the endpoint.

The generated OpenAPI schema (`/api/schema/`) is the machine contract — it never drifts because it
comes from the code. It cannot express flow, business rules or what an error code means to a user.
That is what these files are for. Both exist; neither replaces the other.

## The rule

**An endpoint is not finished until its `.md` is updated in the same change**, and **a new page is
not finished until `docs/api/README.md` maps a path to it.**

Not "later", not "in a follow-up". A merged endpoint without documentation is an incomplete change.

`README.md` is the only file that says which app answers which prefix — a path does not name its
app, and nothing else in `docs/api/` carries that map. A page nobody can find is a page nobody
reads, so `scripts/check-docs.sh` refuses a page no row names. Adding an endpoint to a page that is
already mapped changes nothing there; adding a page does.

## Layout

Flat, one file per app, mirroring `src/`. There is no side directory and no version directory —
`api-drf.md` says why.

```
docs/api/
├── README.md              base URL, auth, error codes, pagination, conventions
├── CHANGELOG.md           dated list of breaking and additive changes
├── accounts.md
├── media.md
└── insights.md
```

`src/media/views.py` → `docs/api/media.md`. Always.

## Language

English, like every document in this repository. Short sentences. No filler, no apology,
no "as you can see".

## Template

Every endpoint section follows the same shape:

````markdown
## Publish a media container

```
POST /api/media/{id}/publish/
```

Publishes a container that has finished processing at Meta. The container is consumed —
publishing the same one twice returns `conflict`, not a second post.

**Auth:** required · **Permission:** `IsAuthenticated`, `OwnsAccount`
**Throttle:** 30/hour

**Request body**

| field | type | required | notes |
|---|---|---|---|
| `caption` | string | no | overrides the caption the container was created with, max 2200 |

**200 OK**

```json
{
  "id": "9f1c8a2e-4d3b-4f77-9c31-6b0a1e5d2f84",
  "instagram_id": "17895695668004550",
  "status": "published",
  "permalink": "https://www.instagram.com/p/C8xYzAbCdEf/",
  "published_at": "2026-09-05T09:12:00Z"
}
```

**Errors**

| status | code | when |
|---|---|---|
| 400 | `validation_error` | `caption` longer than the limit |
| 403 | `permission_denied` | the account belongs to somebody else |
| 404 | `not_found` | no such container, or not one this account may see |
| 409 | `conflict` | already published, or the container is still processing |
| 409 | `publishing_limit_reached` | the account's rolling 24-hour publishing quota is spent |
| 429 | `throttled` | our own rate limit |
| 502 | `upstream_unavailable` | Meta refused or did not answer |

> A container that Meta has not finished processing is not an error the client can retry
> immediately — poll the container's status and publish when it reports finished.
````

## Required content

Each file starts with a one-paragraph summary of the domain and who consumes it.
Each endpoint documents:

- Method and full path, including the `/api/` prefix.
- What it does, in one or two sentences — including side effects (a row written, a token
  refreshed, an object created at Meta).
- Auth, permissions and throttle.
- Request body or query parameters as a table: field, type, required, notes.
  Enum values are listed exhaustively.
- A **real** response example with realistic values. Never `"string"`, never `"..."` in place
  of a field the client must handle.
- Every error the client can receive, with the status, the code, and the condition.
- Pagination shape for list endpoints.
- Business rules the client cannot infer from the schema: limits, resets, ordering,
  what happens on retry.

### Where Meta is involved, say so

Anything the caller would otherwise debug in our code:

- **What is eventually consistent.** A freshly published post that is not yet in the media list is
  Meta's timing, not a bug here.
- **Whose quota is being spent** — ours, the account's, or the app's — and what the client should
  do when it is gone.
- **What we do not proxy.** If an endpoint returns our stored copy rather than a live read, the
  page says so and says how stale it can be.

## Errors and codes

Codes are the contract. `docs/api/README.md` holds the canonical list with a plain-English
meaning for each.

Renaming or removing a code is a breaking change: it goes in `CHANGELOG.md`, and the old code
keeps working until the callers have shipped.

## Changes

`docs/api/CHANGELOG.md`, newest first:

```markdown
## 2026-09-05
- **Breaking** `POST /api/media/{id}/publish/` returns `409 conflict` instead of `400` on a repeat publish.
- Added `permalink` to the publish response.
```

Additive changes are safe. Anything that can break a caller — a removed field, a renamed code, a
narrowed type, a new required field, a changed status — is marked **Breaking**.

## Do not

- Do not paste the OpenAPI schema into these files. Link to `/api/docs/` instead.
- Do not keep a second list of the pages beside the map in `README.md`. Two lists drift.
- Do not document an endpoint that does not exist yet. Write it when it ships.
- Do not leave a `TODO` in a published contract.
- Do not document internal fields or anything the serializer does not return.
- Do not put a real account, token, media id or permalink in an example. Invent it.
- Do not copy Meta's own reference in here. Link to it, and document what **we** do — the two
  drift, and the copy is the one nobody updates.
