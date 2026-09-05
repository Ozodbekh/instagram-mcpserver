---
paths:
  - "src/integrations/instagram/**"
  - "src/**/webhooks.py"
---

# Instagram Graph API

Everything this project does eventually becomes a call to Meta. That call is somebody else's
service, with somebody else's quota, somebody else's uptime and somebody else's deprecation
schedule — and this file is about surviving all four.

**This file is not a reference.** Meta's own documentation is, and it changes. Nothing here is a
number to copy: every limit, metric name, permission and version below is a *shape*, and the value
belongs in configuration or is looked up when it is needed. If you find yourself writing a Graph
API version, a quota or a metric list from memory, stop — that is the mistake this file exists to
prevent.

## Pick one API and write down which

There are two, they are not the same, and confusing them is the most expensive mistake available
here:

| | Reached at | Identity | Tokens |
|---|---|---|---|
| Instagram API with **Instagram Login** | `graph.instagram.com` | an Instagram professional account signs in directly | Instagram user access token |
| Instagram API with **Facebook Login** | `graph.facebook.com` | a Facebook Page linked to an Instagram account | Page access token |

They have different permission names, different id spaces and different endpoints for the same
idea. **`src/integrations/instagram/CLAUDE.md` states which one this project uses, and why.**
Documentation, a tutorial or an answer written for the other one will look almost right and fail
at the third call.

Adding the second one later is a second client behind the same base, never an `if` inside the
first — `core.md`, Open/Closed.

## The version is configuration, and it expires

The version is a path segment (`/v00.0/...`). Meta supports each for a bounded window and then
turns it off; a call to a retired version does not degrade, it fails.

- It comes from `.env` through `root/conf.py`. Never a literal in a URL, never a default in code
  that would silently be wrong.
- **Never write a version number from memory.** Model memory lags Meta's changelog by however long
  it has been. Read the changelog, then set the key.
- One place builds the URL. Grepping for the version must find one line.
- Bumping it is its own change, with the contract tests run against it — never a drive-by edit
  alongside a feature.

## Tokens

An access token is the most dangerous thing this codebase stores. It acts as somebody's business
account, it is bearer-only, and it does not announce that it has leaked.

- **Never logged, never returned, never in an error, never in a tool result** — see `security.md`
  and `mcp.md`. Not truncated, not "just the last four".
- Never in a URL query string. It goes in the `Authorization` header, because a URL is logged by
  every proxy on the way.
- Never in a Celery argument, a cache key or a webhook payload.
- Stored encrypted at rest, or the reason it is not is written in `docs/security-debt.md`.
- A short-lived token is exchanged for a long-lived one at connect time; nothing else in the
  codebase ever sees the short-lived one.

**Refresh before expiry, on a schedule, not on failure.** A long-lived token has a fixed lifetime
and a window in which it may be refreshed. Waiting for a `190` means the account is already broken
and a person has to reconnect by hand.

- The refresh job is idempotent and safe to run twice on the same day.
- It records the new expiry and logs the account id, never the token.
- An account whose token cannot be refreshed is marked, and every selector treats it as
  disconnected. It must not keep failing silently in a loop.
- Refresh has its own quota. A job that walks every account refreshes only the ones inside the
  window.

## Never proxy, never forward

The client owns the whole conversation with Meta.

- **No caller passes a path, an endpoint, a `fields` list or a query parameter through to Meta.**
  Not a view, not a service, not an MCP tool. Every call site names a method on the client, and the
  client builds the request. Forwarding is an open proxy with our token attached.
- The `fields` list is explicit and lives in `constants.py`. The Graph API returns almost nothing
  by default, so a missing field is a silent `None` rather than an error — and a wildcard is a
  privacy decision nobody made.
- The response never leaves the boundary as provider JSON. Translate it into our own model or a
  small dataclass in the client, so a change in Meta's payload breaks one file.

## Rate limits are told to you before they bite

Meta returns usage headers on most calls — the app's, and the business use case's. They report
percentages of the window already spent.

- **Read them on every response and record them.** They are the only warning before a block.
- Back off on the numbers, not on the failure. An app that discovers its limit by being blocked is
  an app that is blocked for the rest of the window.
- A rate-limit error is retried with backoff *only* if the headers say the window has room again.
  Retrying immediately spends the quota that would have recovered.
- Different limits apply per app, per account and per use case, and they are not one counter.
  Which one was hit is in the error, and it belongs in the log line.

## Publishing is two calls and a quota

Create a container, then publish it. The container is not the post — it can be created, take time
to process, expire unused, and fail.

- **Never publish inside a request.** The create-and-poll-and-publish sequence is background work.
  A view or a tool starts it and returns; something else finishes it.
- Poll the container's status. Publishing one that has not finished processing fails, and treating
  that failure as retryable turns into a loop.
- **Check the publishing quota before creating a container, not after.** The account has a rolling
  limit; the endpoint that reports it exists for this.
- Publishing is not idempotent at Meta. Our side is what makes it so: a container id is consumed
  once, recorded as consumed in the same transaction, and a second attempt is `conflict`. Without
  that, a retry is a duplicate post in front of real followers.
- Video and reels processing is slow and its failures are asynchronous. A container that reports a
  processing error carries a reason — store it; the client cannot act on "failed".

## Webhooks

The most dangerous inbound surface here, and the rules are `integrations.md`'s with two Meta
specifics.

- **Verification is a `GET`** carrying a mode, a challenge and a verify token. Compare the verify
  token with `compare_digest` against a value from `.env`, and echo the challenge only on a match.
- **Every `POST` is signed.** The signature is an HMAC over the **raw request body** with the app
  secret. Verify it **before parsing**, against `request.body` — not against a re-serialized dict,
  because whitespace and key order change the bytes and the signature is over bytes.
- Compare with `compare_digest`. Never `==`.
- An empty app secret must refuse every update, never accept one — an empty-string comparison that
  matches is an open webhook.
- Handlers are idempotent: Meta retries, and the same event delivered twice produces one state
  change. Persist the event id and check it inside the same transaction.
- Reply fast and do the work elsewhere. Meta retries on a slow response, so slow work becomes
  duplicate work.
- **The payload is a notification, not data.** Re-read the object through the API rather than
  trusting what arrived — the payload can be stale, partial, or forged if verification is ever
  wrong.

## Errors

A Graph API error is a JSON object with a code, sometimes a subcode, a type, a message and a trace
id.

- Switch on the **code and subcode**. Never on the message: it is written for humans, it is
  localized, and it changes without notice.
- **Log the trace id.** It is the only thing Meta's support can act on, and it is worthless once
  the log line is gone.
- Map every code we handle to one of our own, in one place, and let the rest fall into a single
  `upstream_error`. `api-drf.md` and `mcp.md` both forbid forwarding the provider's text.
- The families worth naming separately, because each needs a different response:
  a **token** failure (the account must reconnect), a **permission** failure (a scope was never
  granted), a **rate limit** (back off), a **validation** failure (our request was wrong), and
  **transient** (retry). Only the last is retryable, and a retry on any of the others burns quota
  to get the same answer.

## Reads are eventually consistent

A freshly published post is not immediately in the media list. Insights lag. A deleted object can
still answer for a while.

Never write a test, a poll loop or a client contract that assumes otherwise. Where an endpoint of
ours reads our stored copy rather than Meta's live answer, `docs/api/` says so and says how stale
it can be — `api-docs.md`.

## Pagination

The Graph API pages with cursors, and a cursor belongs to Meta.

- **A cursor never becomes our page parameter** and is never stored in our database. It expires on
  somebody else's schedule; handing one to our client makes their pagination break for reasons they
  cannot see.
- A sync walks the pages inside the client and returns rows, with a hard cap on pages so a runaway
  history cannot become an unbounded job.

## Insights

- Metric names are not interchangeable across media types, product types or the two APIs above.
  A metric list is per surface and lives in `constants.py`, verified against Meta's reference.
- Some metrics are only available for a bounded recent window. A backfill that asks for older data
  gets an error, not an empty result — that is a validation failure, not a transient one.
- Meta restates numbers. Store the value with the time it was fetched, and treat a changed number
  as normal rather than as corruption.

## Only the documented API

No scraping, no private endpoints, no logged-in session cookies, no unofficial library that wraps
either. It is against Meta's terms, it gets the app banned rather than rate limited, and it takes
the accounts of everyone who connected with it.

If something is not in the documented API, the answer is that the product cannot do it yet.

## Testing

- **Tests never reach Meta.** Every client call is mocked or served by a recorded fixture.
- A contract test per operation pins the request we build and the response we parse — that is what
  catches a version bump.
- Webhook tests cover: valid signature, invalid signature, wrong verify token, replayed event,
  unknown event type, and an empty app secret refusing everything.
- Error mapping is tested per family, from a real error payload shape.

## Definition of done

1. The version and every credential come from `.env`; no literal, no default that would work by accident.
2. The call goes through `src/integrations/instagram/`; no caller passed a path or a field list.
3. Usage headers are read and recorded; the retry policy distinguishes transient from the rest.
4. A publish is idempotent on our side and checks the quota first.
5. A webhook verifies its signature over the raw body before parsing, with `compare_digest`.
6. No token in a log line, a response, a tool result or a task argument.
7. `src/integrations/instagram/CLAUDE.md` says which API this is and what it does not cover.
