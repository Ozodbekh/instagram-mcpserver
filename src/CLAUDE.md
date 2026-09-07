# src

All application code. Configuration is in `root/`, tests in `tests/`.

The name is `src` and not `apps` because not everything here is a Django app: `integrations/`
carries calls out and `webhooks/` carries them in, and neither stores anything.

## What is here

- `accounts/` — connected Instagram accounts and their tokens. The only Django app
- `common/` — shared building blocks that belong to no domain
- `integrations/` — outbound clients. Every third party is reached from here and nowhere else
- `webhooks/` — inbound callbacks from Meta
- `urls.py` — the one module `root/urls.py` includes: a prefix per app

`root/urls.py` reaches this package once and stops there. Adding an app is a line in `src/urls.py`,
never a line in `root/`. No app's own url module carries the `api/` prefix — see
`docs/rules/api-drf.md`.

## Django app or not

A mechanical test:

| | Django app | Not an app |
|---|---|---|
| `models.py` | yes | **no** |
| `apps.py`, in `INSTALLED_APPS` | yes | no |
| may touch `Model.objects` | yes | **never** — calls `selectors` / `services` |
| created by | `startapp` | a hand-made package |

`accounts/` is the only one on the left: a token has to survive a restart and be replaced every
sixty days, so it is a row. The other three persist nothing — `integrations/` carries a call out,
`webhooks/` verifies what arrived and forwards it, `common/` holds the error envelope — so none of
them is installed.

**The test is what decides, and it has already changed one answer.** `webhooks/` was written with a
model first, keyed on a hash of the request body so a redelivery would be recognised, and the model
was removed: the only consequence of a redelivery is a duplicate debug message, while the table
would have stored every stranger's direct message forever. `src/webhooks/CLAUDE.md` records that,
and `docs/security-debt.md` entry 3 says what brings idempotency back.

**A name must never carry models in two places.** An app's label is the last component of its
dotted name, so two apps ending in the same word would collide and Django refuses to start:
"Application labels aren't unique". Each app declares `label` in `apps.py` anyway, even though
Django would derive the same value — it puts the name a foreign key will use next to the app that
owns it.

## Nothing here imports `root.conf`

Application code reads `django.conf.settings`. Importing `root/conf.py` from `src/` runs the
dependency backwards and breaks `override_settings` in tests, because the value was already
captured at import time. See `root/CLAUDE.md`.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file when a directory here appears or disappears.
