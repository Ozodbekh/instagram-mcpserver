---
paths:
  - "src/integrations/**"
---

# Integrations

Everything that talks to a third party lives in `src/integrations/`. Nothing else in the codebase
opens an outbound HTTP connection.

Meta's own rules are in `instagram.md`; this file is what holds for any provider, including that
one.

## Layout

```
src/integrations/
├── base/
│   ├── client.py         timeout, retry, circuit breaker, structured logging
│   ├── exceptions.py
│   └── circuit.py
└── instagram/            the Graph API client, its field lists and its error mapping
```

`src/integrations/` is **not** a Django app. It has no models and no migrations. Anything that must
be persisted — a token, a synced media row, a webhook event id — belongs to a domain app.

That split is what stops the client from growing a memory. A client that stores its own token
becomes the second place tokens live, and the two go out of sync on the first refresh.

## Clients

Every provider client inherits `src/integrations/base/client.py`, so timeout, retry, backoff,
circuit breaking and logging are written once.

Non-negotiable for every outbound call:

- **An explicit timeout.** A call without one can hang a worker forever. Connect and read are
  separate numbers; a provider that accepts the connection and then thinks for five minutes is the
  case a single timeout misses.
- Retry with exponential backoff on transient failures (timeout, 5xx, connection reset) only.
  Never retry a 4xx. Never retry a non-idempotent call without an idempotency key.
- A circuit breaker: after N consecutive failures the provider is skipped and the caller takes
  the fallback path instead of piling up requests.
- Structured logging of provider, operation, latency and outcome — never of the payload,
  never of credentials, never of a token.

## Contracts

- **The provider's response never reaches a view, a serializer or an MCP tool.** Translate it into
  our own model or a small dataclass at the client boundary. A change in their JSON must break one
  file, not twenty.
- Provider errors are wrapped in `src/integrations/base/exceptions.py` types. A domain service
  never catches `httpx.HTTPStatusError` or an SDK-specific exception.
- Where several providers do the same job, they share an abstract base and a registry. The caller
  asks for "the client", not for a brand — `core.md`, Dependency Inversion.

## Configuration

- Base URLs, keys, secrets and API versions come from `.env` through `root/conf.py`. Never a
  literal in code, never a default that would work in production by accident.
- Every new key is added to `.env.example` with an empty value.
- Sandbox and production endpoints are separate configuration values, not an `if DEBUG`.

## Webhooks

Inbound callbacks are the most dangerous surface in the project.

- Verify the signature or the auth header **before** parsing the body, over the raw bytes. An
  unverified webhook is discarded, not logged as an error and processed.
- Compare secrets with `compare_digest`. An empty configured secret refuses every request rather
  than matching an empty one.
- Handlers are idempotent: the same event id delivered twice produces one state change.
  Persist the event id and check it inside the same transaction.
- Reply fast. Do the work in the background; the HTTP response only acknowledges receipt.
- **Never trust the payload's contents.** Re-read the object through the API before acting on it.
- Webhook URLs are unguessable and rate limited.

## Testing

- Tests never reach the network. Every client is mocked or served by a recorded fixture.
- Each provider has a contract test that pins the request we send and the response we parse.
- Webhook tests cover: valid signature, invalid signature, replayed event, unknown event type.

## Definition of done

1. The client inherits the base and declares timeout, retry and circuit breaker.
2. Secrets in `root/conf.py` and `.env.example`.
3. The provider payload is translated into our own type at the boundary.
4. Webhooks verify signatures over the raw body and are idempotent.
5. No network access in tests.
