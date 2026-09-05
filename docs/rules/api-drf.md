---
paths:
  - "src/**/serializers.py"
  - "src/**/views.py"
  - "src/**/urls.py"
  - "src/urls.py"
  - "src/**/filters.py"
  - "src/**/permissions.py"
  - "src/**/base.py"
  - "root/urls.py"
---

# REST API (DRF)

JSON is the only renderer and the only parser. No browsable API, no HTML, no form parser, no
session authentication, no CSRF flow — those belong to a template-rendering site, and this is
not one.

## There are no versions and no sides

**The API is not versioned. There is no `v1/`, no `shared/`, no side directory.** An app is
`src/<name>/` and its endpoints live in that app, flat.

Versioning buys one thing: the ability to change a contract without breaking a client that cannot
be updated. This project has no such client — the consumers are the MCP server in this repository
and whatever calls the HTTP API, both of which ship when we say so. A `v1/` directory here would
be a level of nesting that never holds a second entry, and `YAGNI` in the root `CLAUDE.md` names
exactly that.

If a breaking change ever has to ship beside the old shape, that is the moment to introduce a
version — and the moment to write down in `docs/structure-decisions.md` why. Not before.

The same applies to the MCP surface: an agent connects to the server it is configured against,
and a tool is renamed rather than duplicated.

## Layout

```
src/<app>/
├── CLAUDE.md
├── constants.py       choices, limits, error codes
├── models.py
├── managers.py
├── selectors.py       read queries, scope enforced here
├── services.py        writes and side effects
├── serializers.py
├── permissions.py
├── views.py
├── urls.py            no api/ prefix — the collector owns it
└── migrations/
```

- A view layer never touches `Model.objects`. It calls the owning app's `selectors` / `services`.
- **No app's url module contains the `api/` prefix.** `src/urls.py` collects the apps and
  `root/urls.py` includes that one module, so a prefix change is a one-line edit.
- `utils.py` sits at the app level. One that reads a request or builds a response body is part of
  the contract and belongs beside the views; one that knows neither is an app-level helper. If it
  knows about Meta, it is not a `utils.py` at all — it belongs in `src/integrations/instagram/`.

## Use what DRF already gives you

Before writing a loop, a branch or a helper in a view, check whether the framework already does it.
Hand-rolled equivalents are longer, untested, and invisible to the generated schema.

| Instead of | Use |
|---|---|
| a full `ModelViewSet` with methods disabled | `ReadOnlyModelViewSet`, or compose `ListModelMixin` / `RetrieveModelMixin` / `CreateModelMixin` on `GenericViewSet` |
| overriding `create`/`update` to forbid them | `http_method_names = ('get', 'post', 'patch')` |
| a second endpoint for a state change | `@action(detail=True, methods=('post',))` |
| reading `request.query_params` in the view | `filterset_fields`, or a `FilterSet` in `filters.py` |
| a custom search endpoint | `SearchFilter` + `search_fields` — `^` prefixes an `istartswith` |
| accepting any `?ordering=` value | `OrderingFilter` + `ordering_fields` whitelist |
| slicing a queryset by hand | the pagination class — `pagination_class = None` only for fixed reference sets |
| `if action == 'create': ...` around serializers | `get_serializer_class()` |
| a manual 400 with a message | `serializer.is_valid(raise_exception=True)` |
| a per-view rate limit check | `throttle_scope` with `ScopedRateThrottle` |

**`django-filter` is not installed.** Until it is, a filter that cannot be expressed with DRF's own
backends is written in the selector, never from raw query params in the view.

Two more habits:

- Declare `get_queryset()`, never a module-level `queryset =`. A class attribute is evaluated at
  import time and cannot see `request.user`, so it silently skips scoping.
- Pass `self.get_serializer_context()` whenever a serializer is constructed by hand inside an
  action. Without it the serializer has no `request`, and every context-dependent field breaks.

## Views

Thin. Parse input, call a service or selector, serialize the result.

- No `Model.objects` in a view. Call a selector.
- No business rule in a view.
- **No Graph API call in a view.** A view that would wait on Meta is a request holding a worker
  for as long as somebody else's server takes to answer — see `instagram.md`.
- `permission_classes` is declared explicitly on every view. Never rely on the default alone.
- `self.get_object()` is what runs the object-level permission check. Fetching the row yourself
  inside an action skips it.
- Return `201` on create, `204` on delete, `200` otherwise.

## Serializers

- `fields = '__all__'` is forbidden. List fields explicitly. This is not style: a serializer that
  enumerates its fields is the only thing stopping a synced Graph API column — a token, a raw
  payload, somebody's username — from appearing in a response the day it is added to the model.
- Input and output serializers are separate when they differ. Do not bend one with `read_only`
  gymnastics.
- Field validation in `validate_<field>`, cross-field in `validate`. Business rules that need the
  database live in the service.
- Never write to the database from a serializer. No `create()` / `update()` override carrying
  logic — delegate to a service.
- Nested writes are forbidden. Accept ids, resolve them in the service.
- Never expose internal fields: access tokens, refresh tokens, app secrets, raw provider payloads.

## URLs

`SimpleRouter` for viewsets, explicit `path()` for one-off endpoints. Lowercase, plural nouns,
trailing slash: `/api/accounts/`. Actions are sub-paths, not verbs in the collection name:
`/accounts/{id}/refresh-token/`. Never expose a sequential primary key where enumeration
matters — use the public id.

**A Meta id is never a URL segment of ours.** It identifies an object on somebody else's platform
and says nothing about who may read it here; route on our own id and let the selector do the rest.

## Errors

Responses carry a machine-readable **code**, never a human sentence — the UI maps codes to
messages.

```json
{"code": "validation_error", "errors": {"caption": ["max_length"], "media_url": ["required"]}}
```

- Implemented once, in `src/common/exceptions.py`, wired as DRF's `EXCEPTION_HANDLER`.
- Codes are `snake_case`, stable, and documented in `docs/api/README.md`. Renaming one is a
  breaking change.
- Standard codes: `not_authenticated`, `permission_denied`, `not_found`, `throttled`,
  `validation_error`, `conflict`.
- **A Graph API failure is translated, never forwarded.** Meta's `error.message` is written for
  our developers, changes without notice, and sometimes names an internal id. Map its
  `error.code` / `error_subcode` to one of ours and log the rest — `instagram.md` holds the
  mapping.
- Never return a stack trace, a database message or a provider's raw error.

## Pagination, filtering, ordering

- Default pagination is `src/common/pagination.py` (page size 20, max 100). Every list endpoint is
  paginated — no unbounded list.
- Ordering is whitelisted via `ordering_fields`. Never accept an arbitrary column name.
- **Never paginate an unordered queryset.** Without an `ORDER BY` a row can appear on two pages.
- Our pagination is over our own rows. Meta's cursor pagination stops at the integration boundary
  and never becomes our page parameter — a client of ours must not be handed a cursor that
  expires on somebody else's schedule.

## Schema

Generated by `drf-spectacular` from serializers, views and urls: `/api/schema/`, Swagger at
`/api/docs/`. Never hand-edit it — if it is wrong, the serializer or the view is wrong. Use
`@extend_schema` only for what the code cannot express. The generated schema is the machine
contract; the human contract is `docs/api/**.md`, and it is mandatory — see `api-docs.md`.

## Definition of done

1. Logic is in `services.py` / `selectors.py`, not in the view.
2. Permissions are explicit and tested.
3. Errors return codes from the shared handler; no Meta error text reaches a client.
4. Tests cover happy path, validation error, unauthenticated, and forbidden.
5. `docs/api/<app>.md` is updated in the same change, and `docs/api/README.md` maps the path to it.
6. The app's `CLAUDE.md` describes the endpoint's meaning and its business rules.
