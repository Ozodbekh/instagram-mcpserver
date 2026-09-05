---
paths:
  - "src/**/services.py"
  - "src/**/selectors.py"
  - "src/**/tasks.py"
  - "src/**/signals.py"
---

# Services and selectors

Business logic lives in exactly two modules per app: `selectors.py` **reads** and never writes;
`services.py` **writes** — create, update, delete, state transitions, side effects.

Every caller goes through them — DRF views, MCP tools, management commands. **That is why the
logic is written once**, and in this project it is the whole point: an MCP tool and a REST
endpoint that publish a post must not be able to disagree about what publishing means.

Nothing in this layer knows about HTTP: no `Request`, no `Response`, no status codes, no
serializers, no `request.user` — the caller passes the user in as `actor`.

Nothing in this layer knows about MCP either: no `ToolError`, no FastMCP context, no scope check.
A service raises a domain error and the tool translates it, exactly as a view does.

## Services

A service is a module-level function. That is the default and covers almost everything.

- Keyword-only arguments (`*` first). The first is `actor` when the action has an author.
- Return a model instance or `None`. Never a dict, never a serialized payload.
- **Return only what a caller reads.** A service a signal or a task calls usually returns `None`.
  The cost is not the value — it is the promise: a declared `-> bool` invites a caller to depend on
  it, and the next person cannot tell whether anything already does.
- Validate, then act. Raise `ValidationError` with field codes.
- Wrap multi-statement writes in `atomic`; schedule side effects with `on_commit`.
- One function, one business action. `media_publish` does not also refresh the token — it calls
  the service that does, or fails and says which.

## Selectors

- Return a `QuerySet`, not a list — the caller paginates.
- Apply visibility and scope rules here, using `src/common/scope.py`. A selector never returns rows
  the actor may not see. **An MCP tool reads through the same selector a view does**, so a row an
  agent must not see is unreachable by construction rather than by a check somebody remembered.
- Reusable filters belong in `managers.py` as queryset methods, not duplicated across selectors.
- **A selector never writes.** Not a `get_or_create`, not a `last_synced_at` touch. If reading
  needs a row that may not exist, the caller's service makes it, or the selector answers for its
  absence.

## A service never calls Meta directly

An outbound Graph API call goes through `src/integrations/instagram/`, and only through it — see
`integrations.md`. The service decides *what* to publish and *whether* it may; the client decides
how to speak to Meta.

Two consequences that are easy to get wrong:

- **A Graph API response never reaches a serializer or a tool.** The client translates it into our
  own model or a small dataclass at the boundary, so a change in Meta's JSON breaks one file.
- **The service owns the transaction; the client is outside it.** An HTTP call inside `atomic`
  holds a database connection for as long as somebody else's server takes to answer. Do the call,
  then open the transaction — or write the row first and reconcile, and say in the app's
  `CLAUDE.md` which of the two it is.

## Classes only for polymorphism

Use a class when there are genuinely several interchangeable implementations chosen at runtime.
That is Open/Closed and Dependency Inversion doing real work, not decoration.

- The base class is abstract and small. No method exists on it that a subclass must reject with
  `NotImplementedError` — split the base instead.
- Callers depend on the base type and receive the implementation from a registry or factory.
- Adding an implementation means adding a file, never editing an existing one.

Do **not** create `MediaService` / `MediaSelector` classes that only group functions. A module
already is that grouping, and a class there adds `self` for nothing.

## Naming

`<noun>_<verb>`: `media_publish`, `account_connect`, `insight_list`, `token_refresh`. The noun
first is what makes the module greppable by domain, and it sorts related functions together.

## Crossing apps

A service may call another app's **public** service or selector. Import the public function, never
an internal helper. If two apps need each other, the shared piece belongs in `src/common/`.

## Boundaries checklist

- No query in `views.py`, in a serializer, or in an MCP tool.
- No `Response`, `status` or `Request` inside `services.py` / `selectors.py`.
- No `httpx`, `requests` or Graph API URL inside `services.py` / `selectors.py`.
- No app imports another app's internals.
- No circular import between packages under `src/`.
