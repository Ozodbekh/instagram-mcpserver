---
paths:
  - "docs/rules/core.md"
---

# Core

The rules themselves are in the root `CLAUDE.md`, in one line each, and that is the copy to obey.
This file is the reasoning and the worked examples behind the ones that are argued with most —
open it when a rule looks wrong, not before.

## No comments

If code needs a comment to be understood, the name is wrong or the function is too big. Rename it
or split it.

```python
def d(m, t):
    x = m.timestamp
    return (t - x).days


def days_since_publish(media, at_date):
    return (at_date - media.timestamp).days
```

The only non-code text allowed is `# type: ignore[...]` or `# noqa: <code>` naming the specific
rule, when a tool is provably wrong.

**Uzbek is for text a person reads with no UI in between** — an email, a Telegram push — and it
lives in the app's `constants.py`, never inline and never in a choice label or a column. The UI
localizes; the backend ships codes.

## Extraction is not free

Every function is a jump the reader must take. Extract when the jump pays for itself; otherwise
keep the code where it is. "Small functions" bounds size — it does not mean every statement
deserves a name.

Extract when **any** of these is true:

- A second caller exists. Not "might exist" — exists.
- The function mixes levels of abstraction, or breaks the size and nesting limits.
- The block is a business rule that deserves a test of its own.
- The block is an outbound call or a clock — something a test will replace.

NEVER extract when:

- The body is one line or one expression with one caller. Name a **local variable** instead — it
  explains just as well and costs no jump.
- The helper would sit beside its only caller and read the same inlined.
- The wrapper only renames a single ORM or library call. `Model.objects.create(...)` called once is
  not a service, and a receiver creating a row needs no function to call.
- The split exists to dodge the no-comments rule. A comment problem is a naming problem, and a
  well-named local solves it in place.

```python
def _is_publishable(container):
    return container.status == FINISHED


def media_publish(*, actor, container):
    if not _is_publishable(container):
        raise ValidationError({'container': ['not_finished']})


def media_publish(*, actor, container):
    if container.status != ContainerStatus.FINISHED:
        raise ValidationError({'container': ['not_finished']})
```

The reading path is bounded at both ends: a view or an MCP tool calls a service, a service calls
selectors, models and integrations — the whole flow is visible in **two jumps**. Ten three-line
private helpers hide the flow as thoroughly as one sixty-line function; both are wrong.

When in doubt, keep it inline. Inlining a helper later is a rename; reassembling a rule that was
scattered across five helpers is archaeology.

The same applies to what a function hands back. **Returning a value nobody reads is a promise, not
a courtesy** — a declared `-> bool` invites a caller to depend on it, and the next reader cannot
tell whether one already does.

## Imports

Import the names you use, not the parent module, and call them with no prefix. This holds for every
library, not only Django.

| Instead of | Write |
|---|---|
| `from django.db import models` → `models.CharField` | `from django.db.models import CharField` |
| `from rest_framework import serializers` → `serializers.ModelSerializer` | `from rest_framework.serializers import ModelSerializer` |
| `from rest_framework import status` → `status.HTTP_201_CREATED` | `from rest_framework.status import HTTP_201_CREATED` |
| `from django.db import transaction` → `transaction.atomic` | `from django.db.transaction import atomic, on_commit` |
| `import logging` → `logging.getLogger` | `from logging import getLogger` |
| `import os` → `os.environ` | `from os import environ` |

Two exceptions, and only these: a name that would collide or lose its meaning alone
(`from datetime import datetime` is fine; a bare `date` next to a model field called `date` is
not — import the module there), and **generated files** — migrations keep whatever style
`makemigrations` produced and are never hand-edited to satisfy this.

An import inside a function is allowed only to break a real cycle — and a cycle means the layering
is wrong, so fix that first.

## SOLID, in this codebase

| | What it means here |
|---|---|
| **S** | One module, one job. `services.py` writes, `selectors.py` reads, `views.py` speaks HTTP, a tool speaks MCP. A function that both publishes a post and refreshes a token is two functions. |
| **O** | Adding a second Graph API surface must not edit the existing client. New file, same base class, register it. |
| **L** | A subclass is usable wherever the base is. Never narrow a signature or raise where the base returned. |
| **I** | A client that only reads insights must not inherit a `publish()` it raises `NotImplementedError` on. |
| **D** | Depend on the base client, not on the concrete one. Callers receive the abstraction; a factory picks the implementation. |

## Inheritance and MRO

Inherit only for a real **is-a**; otherwise compose. Depth ≤ 2 below our own base — deeper means the
hierarchy is wrong. Always `super()`, never the parent class by name. Cooperative multiple
inheritance is only for mixins that all call `super()`, mixins first and the concrete base last:

```python
class InstagramAccount(SoftDeleteMixin, TimeStampedModel):
    ...
```

If you cannot state a class's MRO out loud, flatten it. Never use `super()` inside the `__init__`
of a mixin that changes the signature.

## Magic values

Every literal that is not `0`, `1` or `''` goes to `constants.py` — the app's own if one app uses
it, `src/common/constants.py` once a second does.

```python
if account.published_today > 25:
    ...

if account.published_today > CONTENT_PUBLISHING_DAILY_LIMIT:
    ...
```

The second is greppable, changeable in one place, and says what the number means. The first is a
number somebody will be afraid to change.

This matters more here than in most projects: nearly every number in this codebase is **Meta's**,
not ours — a publishing quota, a token lifetime, a rate-limit window, a Graph API version. A
named constant is where the next reader learns which side of the boundary a number came from,
and `instagram.md` says which of them are configuration rather than constants.

## Principles

**KISS** — the simplest thing that works. No design pattern without a second caller that needs it.

**YAGNI** — nothing built for a requirement nobody asked for: no `**kwargs` passthrough "for
later", no abstract base with one implementation, no API version directory before a breaking
change exists, no feature flag for a feature that ships on.

**DRY** — the same rule expressed twice will drift. Move it to `src/common/` once a **second** app
needs it, and not before, because moving it earlier is YAGNI.

Those two pull against each other on purpose. DRY says share it; YAGNI says wait for the second
caller. The second caller is what settles it.
