---
paths:
  - "src/**"
  - "root/settings.py"
  - "root/conf.py"
---

# Security

This project holds **other people's access tokens**. A token here acts as somebody's Instagram
business account: it can read what that account can read and post in that account's name, in front
of their audience, and it carries no second factor. Losing one is not an incident that gets
explained — it is somebody's business account publishing something they did not write.

Every rule here is blocking, and this file wins when another conflicts with it. Where a decision
forces a weaker rule, the gap goes in `docs/security-debt.md` with what would unblock it — never
left implicit. Dependency weighting at a security boundary is in `dependencies.md`.

## Secrets and tokens

- Never in code, a migration, a fixture, a test, a commit or a log line. All of them come from
  `.env` through `root/conf.py`, typed `SecretStr`; new keys go into `.env.example` with an empty
  value.
- A committed secret is rotated, not deleted.
- `DEBUG = False` in production, `ALLOWED_HOSTS` explicit — never `['*']` outside local.

**An access token is never:**

| Never | Because |
|---|---|
| logged, even truncated | logs are copied, shipped and read by tools |
| returned by an endpoint | there is no caller that needs it |
| returned by an MCP tool | it lands in a model's context, a transcript and a provider's retention |
| put in a URL or query string | every proxy on the path logs the URL |
| put in a task argument or a cache key | both sit in a broker and echo in monitoring |
| sent to an error tracker | a traceback carries locals |
| copied into a second table | two copies diverge on the first refresh |

Stored encrypted at rest, or the reason it is not is an entry in `docs/security-debt.md`.

**An empty secret must fail closed.** `compare_digest('', '')` is `True`, so a webhook secret that
defaults to `''` accepts a request that sends no signature at all. Every secret used in a
comparison either has no default and refuses to start, or is checked for emptiness before the
comparison.

## Authorization

- `permission_classes` is declared explicitly on every view, every action and every MCP tool.
  Never rely on a default.
- **Object-level access is enforced in the selector, not the view.** A user must not read another
  user's account, media, insight or token by guessing an id.
- Scope rules live once, in `src/common/scope.py`, and are used by REST and MCP alike. A field
  hidden in one surface is hidden in all of them.
- MCP scopes are separate powers, not a ladder: reading, writing and publishing are three, and
  there is no wildcard — `mcp.md`.
- User-facing objects are addressed by an unguessable public id. Sequential integers invite
  enumeration.
- **A Meta id proves nothing.** Anyone can read an Instagram account id off a public profile. It
  identifies an object on somebody else's platform; who may touch it here is our own row.

## Connected accounts

- An account is connected by its owner going through the documented OAuth flow. There is no path
  that attaches an account to a user without that.
- The OAuth `state` parameter is random, single-use, bound to the session that started the flow,
  and checked on return. Without it the callback is a CSRF hole that connects an attacker's
  account to somebody else's user — or the reverse.
- The redirect URI is an exact configured value. Never built from a request parameter.
- Disconnecting revokes at Meta and deletes our copy of the token in the same change. A row marked
  disconnected while the token still works is a token nobody is watching.

## Personal data

- Never log account handles, follower lists, direct message contents, comment bodies or the
  captions of private accounts. Log ids.
- Data we pulled for one purpose is not reused for another. An insight sync does not become a
  follower database.
- Deleted accounts are purged, tokens included, and the purge is a job that can be proven to have
  run.

## Input

- All input is validated by a serializer or a typed tool argument. No `request.data` reaches a
  service unvalidated.
- Never build a query from raw user input: no `**request.query_params`, no `.extra()`, no `raw()`
  with interpolation, no user-supplied `order_by`.
- **Never build a Graph API request from caller input** — no forwarded path, endpoint, field list
  or parameter. `instagram.md` says why: it is an open proxy with our token attached.
- Uploads: whitelist content types, cap the size, verify the real type from the bytes, strip EXIF
  (it carries GPS), and re-encode. Never trust the filename or the extension.

## Text a stranger wrote is hostile

Captions, comments, bios and direct messages arrive from the open internet. They are the cheapest
attack surface this product has, and they land in two places that execute meaning: an AI model's
context, and anything that renders them.

- In an MCP tool result: delimited, length-capped, and never presented as instruction — `mcp.md`.
- In a prompt: the same, and never interpolated raw.
- Anywhere rendered: escaped.

A tool that summarises comments is a prompt-injection surface. Treat it as one, and say so in its
description.

## Rate limiting

Mandatory on the OAuth callback, the token endpoint of the MCP server, the webhook, and every
endpoint that causes an outbound Graph API call.

The last one is not about abuse of us — it is about **our quota at Meta being a shared, exhaustible
resource**. One caller in a loop takes every connected account offline for the rest of the window.

## External calls

- Every outbound call has a timeout — see `integrations.md`.
- **Webhook signatures are verified before the body is parsed**, over the raw bytes, and handlers
  are idempotent.
- Never trust a webhook payload's contents. Re-read the object through the API.

## Logging

- Standard library, `getLogger(__name__)`, never `print`.
- Structured values in `extra`, never formatted into the message: `extra={'account_id': id}` is
  queryable, `f'account {id} failed'` is not.
- `logger.exception(...)` inside an `except` block. Never `logger.error(str(exc))`, which throws
  the stack away.
- Log Meta's trace id on a Graph API failure — it is the only thing their support can act on.
- Never log a token, a signature, an `Authorization` header, or a provider payload.

## Errors

Responses return codes, never stack traces, database messages or provider errors. A Graph API
error is mapped to one of ours — `instagram.md`.

## Definition of done

1. Explicit permissions on the view or tool, and object-level scope in the selector.
2. No secret, token or personal data in any log line, response or tool result.
3. Input validated; no raw input in a query and none forwarded to Meta.
4. A throttle if the endpoint is on the list above.
5. A test proves another user cannot read or modify the object.
