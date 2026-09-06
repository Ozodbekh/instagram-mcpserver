# integrations

Every outbound call leaves from here. Nothing else in the codebase opens an HTTP connection —
`docs/rules/integrations.md`.

Not a Django app: no models, no migrations, not in `INSTALLED_APPS`. It carries a call out and
decides nothing.

## Status

One provider, `telegram/`. The Instagram Graph API client does not exist yet — today Meta only
talks **to** us, through `src/webhooks/`.

## There is no `base/` yet

`docs/rules/integrations.md` says every client inherits a shared base carrying timeout, retry and
circuit breaking. With one provider that base would be an abstract class with one implementation,
which the root `CLAUDE.md` forbids under YAGNI.

The two rules do not actually disagree: the base earns its place at the **second** provider, and
that is the change which creates it. Until then `telegram/client.py` declares its own timeout, and
what it deliberately does not do is written down beside it.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file when a provider appears or disappears.
