# common

Building blocks that belong to no domain. A piece moves here when a **second** caller needs it, and
not before — `docs/rules/core.md`, DRY against YAGNI.

## Status

No models, and **not in `INSTALLED_APPS`** — `exceptions.py` and `constants.py` only. Django
resolves `EXCEPTION_HANDLER` by importing the dotted path, not through the app registry, so
installing it would buy nothing today. It becomes an app in the change that adds its first model.

## Why it exists before a second app does

The error envelope is not an app's decision. `docs/api/README.md` publishes
`{"code": ...}` as the contract every endpoint answers in, and a handler added later would change
the shape of every endpoint at once. It is wired globally as DRF's `EXCEPTION_HANDLER` from the
first endpoint, so nothing has to migrate.

## The envelope

`coded_exception_handler` rewrites whatever DRF produced into a machine-readable code and nothing
else. No sentence reaches a caller.

| Raised | Answered |
|---|---|
| `ValidationError` | `{"code": "validation_error", "errors": {...}}` |
| `DomainError(code, status)` | `{"code": code}` with that status |
| any other DRF exception | `{"code": <its default_code>}` |
| `Http404`, Django's `PermissionDenied` | `not_found`, `permission_denied` |
| anything else | untouched — Django turns it into a 500 |

`DomainError` is what application code raises when the failure has a name of its own:
`DomainError('invalid_signature', HTTP_403_FORBIDDEN)`. It carries the status because the status is
part of the same decision, and splitting them puts half of it in the view.

The handler reads `default_code` rather than the exception's message, so a DRF release that reworded
`"Authentication credentials were not provided."` changes nothing on the wire.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file after finishing work here.
