# integrations

Every outbound call leaves from here. Nothing else in the codebase opens an HTTP connection —
`docs/rules/integrations.md`.

Not a Django app: no models, no migrations, not in `INSTALLED_APPS`. It carries a call out and
decides nothing.

## Status

Two providers. `telegram/` sends the delivery forwarder's messages out; `instagram/` exchanges and
refreshes access tokens. Meta also talks **to** us, but that arrives through `src/webhooks/` and
never through here.

## There is still no `base/`, and the earlier note was wrong about why

That note said the base arrives with the second provider. The second provider is here and the base
is not, because "a second provider" was never the real trigger — a second caller **that needs the
abstraction** is, exactly as `docs/rules/core.md` puts it.

`docs/rules/integrations.md` wants the base to carry timeout, retry, backoff and circuit breaking.
Neither client retries: Telegram deliberately does not, because its only caller is inside a request
Meta is waiting on, and Instagram does not, because its only caller is a daily cron working a
ten-day window. Strip retry and circuit breaking out and what is left to share is building a URL
and passing a timeout tuple — two lines, in two files whose shapes already differ (one `POST` with
a JSON body, one `GET` with query parameters), wrapping two completely different error formats.

**The base arrives with the first client that needs retry with backoff** — the first one a person
is waiting on. That is the change which creates it.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file when a provider appears or disappears.
