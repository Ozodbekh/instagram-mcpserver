---
paths:
  - "src/mcp_server/**"
---

# MCP server

`src/mcp_server/` exposes a controlled slice of the backend to AI agents over the Model Context
Protocol. **It is the point of this project**, not a side door onto it: the REST API and the MCP
surface are two ways into the same services, and neither may know something the other does not.

It runs as its own process, sharing the database and the code but not the request cycle, and it is
in `INSTALLED_APPS` so the ORM and migrations work.

The directory is `src/mcp_server/`, never `mcp/`: a top-level `mcp/` package would shadow the
installed `mcp` SDK that the server is built on.

## The SDK is `fastmcp`

`fastmcp` provides the server, the Streamable HTTP transport, and the tool decorator. We write the
glue — Django setup, client credentials, the JWT, the middleware — and every tool by hand.

**Not `django-mcp-server` or `mcp-django`.** Both are built around exposing models and querysets as
tools automatically, which bypasses the selector layer where this project decides who may see which
rows. Constraining either back to our rules leaves the same amount of glue plus a dependency.

**Not a hand-written protocol implementation.** MCP is JSON-RPC 2.0 plus capability negotiation,
Streamable HTTP, cancellation, progress, resources, prompts and sampling. The value of an SDK is
being tested by thousands of clients, not being written.

**What using `fastmcp` costs, and what pays for it.** It is a fast-moving layer sitting on the most
security-sensitive boundary in the codebase, and its tool-generation and proxying features are ones
this project deliberately does not use. That is accepted, and it is the reason the rules below are
not optional: every tool is written by hand against selectors, every result is bounded, and no
destructive action is exposed. The framework is not what keeps data in; those rules are.

## Layout

```
src/mcp_server/
├── main.py             Django setup, then the Starlette app and the FastMCP mount
├── middleware.py       deny by default; only the open paths pass without a bearer
├── http_auth.py        the JWT it mints and verifies, and the scope guard tools call
├── constants.py        error codes, scopes, limits
├── models.py           MCPClient — the credentials an agent presents
├── selectors.py        the client a bearer names, and whether an address is throttled
├── services.py         mints a client and its one-time secret, and authenticates one
└── tools/              one module per domain, and the tuple main.py registers
```

## Authentication

- A client presents `client_id` and `client_secret` and receives a JWT. The secret is stored only
  as a PBKDF2 hash and is never recoverable, and the token endpoint is throttled — one attempt
  costs hundreds of thousands of iterations, so an open endpoint is a CPU amplifier as much as a
  guessing target.
- The middleware is **deny by default**: an explicit list of open paths passes, everything else
  needs a valid bearer, routed or not. There is no anonymous mode, not even in development.
- **The signing key is the MCP server's own**, never Django's `SECRET_KEY`. Pin the algorithm,
  check an issuer and an audience, and require the claims you read.
- Catch `PyJWTError`, not `DecodeError`. `InvalidAlgorithmError` is not a `DecodeError`, so a
  narrower catch turns a forged `alg` into a 500 instead of a refusal.
- **The secret comes from `django.conf.settings`, like everything else under `src/`.** Nothing here
  may import `root.conf` — see `root/CLAUDE.md`.
- Bind to loopback unless a TLS terminator is in front. The bearer travels in clear.

## Scope

- **A token carries identity, never authorisation.** Scopes are read from the client's row on every
  request, so disabling a client or narrowing its scopes takes effect on the next call instead of
  when the token expires. A token that carries its own scopes is a token that cannot be revoked.
- **Scope is checked inside the tool**, not only at connect time. Authenticating proves which
  client is calling; it does not decide what that client may do.
- A tool that does not check a scope is a tool every client can call.
- Scopes are an enum the create service validates against. **No wildcard** — one scope that opens
  every tool re-opens everything the checks were added for.
- Read and write are different scopes, and **publishing is its own scope again**. Reading an
  account's media and posting to that account in front of its followers are not the same power,
  and a client that only needs the first must not receive the second.

## Tools

- One tool, one job, one clear name: `media_list`, not `do_instagram_stuff`.
- **A tool is a plain function in `tools/`, never a decorated one in `main.py`.** `tools/__init__.py`
  names the set and the composition root registers it, so the file that wires the transport does not
  also hold the surface — and a tool stays callable, and testable, without a server.
- **`async def` only when the body awaits something.** A sync tool is dispatched to a worker
  thread; an async one runs on the event loop, so an `async def` doing blocking work — a file read,
  a sync ORM call, an outbound request — stalls every other request the process is serving, and
  looks fine until it is under load. A tool that reaches a selector is `async def` with
  `await sync_to_async(...)`, because the ORM is sync too.
- The description is the contract the model reads. State what it returns, what it does **not** do,
  and when not to call it. A vague description produces wrong calls.
- Arguments are explicitly typed and validated. Never accept a free-form filter, a raw SQL
  fragment, an ORM lookup string, a path, or **a raw Graph API field list or endpoint path** — a
  tool that forwards what the model wrote is an open proxy onto Meta with our token attached.
- A tool calls `selectors.py` / `services.py`. It never writes a query, never touches
  `Model.objects`, and never calls the Graph API itself — the visibility rules that protect REST
  must protect it too.
- Read tools and write tools live in different modules and require different scopes.
- Every write tool is idempotent where possible and records who invoked it: the acting agent is
  stored on the audit trail like a human actor.

## What is not exposed

**Destructive and irreversible actions are not tools.** A tool may prepare or recommend one; a
human confirms it.

For this project that list is concrete and it is not negotiable:

- **Deleting a post, a comment or an account.** Gone at Meta is gone.
- **Disconnecting an account or revoking a token.**
- **Anything that spends money** — boosting, promoting, an ads call.
- **Replying or commenting as the account holder** without a human in the loop. A published word
  in somebody's name is not undoable by an apology.

Publishing itself is exposed only behind its own scope, and an app that turns it on says so in
`src/mcp_server/CLAUDE.md` with what confirms a publish.

Where a tool ships before its scope check does, the gap goes in `docs/security-debt.md` with what
would close it — never left implicit.

## Data safety

- Tools never return credentials. **No access token, no refresh token, no app secret, no
  `client_secret`** — not truncated, not "for debugging", not in an error. A token in a model's
  context window is a token in a log, a transcript and a provider's retention window.
- Tools never return personal data the task does not need: no follower lists, no direct message
  contents, no email addresses harvested from a profile. Return ids and counts.
- Results are bounded — a maximum row count and payload size, enforced in the tool. Truncation is
  reported in the response, never silent.
- Free text written by other people — captions, comments, bios, direct messages — is **untrusted
  input**. It arrives from the open internet, it is the one thing on this platform an attacker
  controls for free, and it lands directly in a model's context. Return it delimited, length-capped,
  and never let it act as an instruction. A tool that summarises comments is a prompt-injection
  surface; treat it as one.
- Nothing a tool returns is logged in full. Ids in `extra`, never formatted into the message.

## Errors are codes

A tool raises `ToolError` with a code from `constants.py`, never a sentence and never a provider's
message. A Graph API failure is mapped the same way it is for REST — see `instagram.md`. The model
reads the code; a human reads the log.

## Documentation

Documentation the agent reads before acting — what a tool means, what a status means, which
quotas apply — is served out of this repository, so there is one copy and it cannot go stale.

**Serve a catalogue, never a path.** Expand an allow-list of globs into repository-relative paths
and accept only a key of that mapping. There is then nothing to traverse and no prefix check to
slip past, and one refusal covers unknown, forbidden and absent alike — two different refusals tell
a caller which files exist.

**Cut the catalogue to the audience.** Serve the contract and what a client can observe, never the
engineering rules, the models or the constraints. `docs/security-debt.md` and
`docs/structure-decisions.md` stay out of every catalogue: one is the inventory of what is not yet
fixed, the other of what is not yet decided. A second audience is a second scope and a second
catalogue.

## Definition of done

1. The tool has a precise name, a complete description and typed arguments.
2. It goes through selectors or services, with the same scope rules as REST.
3. It requires a scope and checks it; write and publish tools require their own.
4. The response is bounded, carries no credential, and delimits every piece of text a stranger wrote.
5. Destructive actions are not exposed.
6. Tests cover allowed scope, missing scope, and oversized result truncation.
7. `src/mcp_server/CLAUDE.md` lists the tool and says what it means.
