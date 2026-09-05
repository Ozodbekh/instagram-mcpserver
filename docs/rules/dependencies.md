---
paths:
  - "pyproject.toml"
  - "uv.lock"
---

# Dependencies

Managed by `uv`. `uv.lock` is committed; it is what pins versions, and it is the only thing that
does.

## A version is never written by hand. Anywhere. For any reason.

```
uv add djangorestframework==3.18.0
uv add "djangorestframework>=3.18"
uv add djangorestframework~=3.18
uv add djangorestframework
```

Only the last form is allowed.

`uv add` then writes a lower bound of its own — `"django>=6.1.1"`. That is uv's work, not a hand
written version, and it is a floor rather than a pin: `uv` still resolves upward from it. Leave it
exactly as uv wrote it.

- Never edit `pyproject.toml` to add, raise or lower a version.
- Never copy a version from documentation, a tutorial, an answer or from memory. Every such number
  is a snapshot of the past, and writing it installs an old release on purpose.
- If you believe you know a package's current version, you do not. Model memory lags the index.
  `uv` resolves the newest compatible release; that is its entire job.
- A version that must be known is checked against PyPI, never recalled.
- When something breaks after an upgrade, fix the code. Pinning to hide a break leaves the project
  stuck on a release that stops receiving security fixes.

The same rule, for the same reason, governs the **Graph API version** — which is not a package but
is recalled just as wrongly. It is configuration, read from the changelog, never written from
memory. See `instagram.md`.

## Runtime or development

The server installs with `uv sync --no-dev`, so anything in the development group is absent in
production. Getting the side wrong either ships a test library to the server or breaks the deploy.

Do not guess from the package's reputation. Answer two questions, in order:

**1. Is it imported by any file under `src/` or `root/`?**

```
grep -rn "^from <module>\|^import <module>" src/ root/
```

A hit means runtime — `uv add <name>`.

**2. Is it required by the running application even though our code never imports it?**

That covers infrastructure the stack loads by name or by process: a database driver, the ASGI
server, a cache backend, a monitoring agent. A backend named as a string in `settings.py` is
imported by Django, not by us — it is still runtime.

**Neither?** Then it is development — `uv add --dev <name>`.

That is everything imported only from `tests/`, everything invoked as a command rather than
imported (`pytest`, `ruff`, `mypy`), and every `*-stubs` package, which the type checker reads and
nothing ever imports. Stubs in the runtime list are the usual mistake.

The check after adding is the same grep: no hit under `src/` or `root/`, and not on the
infrastructure list above, means it is in the wrong group.

## Before adding anything

- Confirm it supports Django 6.1 and Python 3.14 — check PyPI, do not assume.
- Look at what it pulls in with it. A one-line convenience that drags in a dozen transitive
  packages is not a convenience.
- Prefer the standard library. Prefer what Django already ships.
- **A dependency at a security boundary is weighed harder** — auth, the MCP transport, the HTTP
  client that carries our tokens, anything that touches a webhook signature. Fewer layers between
  the wire and our own code.
- **Never an unofficial Instagram library.** The ones that wrap private endpoints or a logged-in
  session violate Meta's terms and get the app banned rather than rate limited — `instagram.md`.
  A wrapper around the *documented* API is judged like any other dependency, and usually loses to
  a client we can read.

## Removing

`uv remove <name>` when the last import goes. A package left behind after the code that used it
was deleted is still installed, still updated, and still part of the attack surface.

## Definition of done

1. Added with `uv add` or `uv add --dev`, with no version specifier.
2. In the correct group, verified by the grep above.
3. `pyproject.toml` untouched by hand; `uv.lock` committed alongside it.
