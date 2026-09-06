# Security debt

The gaps between `docs/rules/security.md` and what the code does today, in one place. The details
live where each entry points — this file exists so nothing is forgotten, not to hold a second copy.

**Update this file in the same change that fixes, adds or accepts an entry.**

## Accepted while building — must not reach production

1. **Every Instagram webhook delivery is forwarded to one Telegram chat, in full.** Comment text and
   direct message contents therefore leave this system and land in a chat, a Telegram server and
   somebody's phone. `security.md` says never to log direct message contents; forwarding them is
   worse, because a log is inside our boundary and this is not.

   It is deliberate: it is how a person watches what Meta sends while the integration is being
   built, and there is nothing else to watch it with yet. Nothing is stored on our side — the
   Telegram chat is the only copy, and it is the whole point.

   **What removes it:** `TELEGRAM_DEBUG_CHAT_ID` empty already refuses to send, so the feature is
   off by configuration. Deleting `instagram_delivery_forward` and `src/integrations/telegram/`
   removes it for good. That happens when there is a real reader of these events — the MCP surface,
   or a UI.

2. **The webhook is not throttled.** `security.md` makes it mandatory. It is absent because DRF's
   throttle answers `429` and Meta redelivers on any non-`200`, so throttling converts a burst into
   a larger one. The signature check bounds the work an unsigned request can cause — one
   HMAC-SHA256 over the body — and that is cheap.

   **What closes it:** a rate limit in the reverse proxy, which drops the request before it reaches
   the application and never teaches Meta to retry harder.

3. **The webhook is not idempotent.** `instagram.md` requires a handler to persist an event id and
   refuse a redelivery. This one forwards a duplicate Telegram message instead, because that is the
   entire consequence today and the alternative is storing every payload — see
   `src/webhooks/CLAUDE.md`.

   **What closes it:** the first handler with a real side effect. Idempotency arrives with it, keyed
   on whatever that handler actually needs rather than on the whole body.

## Not yet decided

4. **Access tokens are not stored at all yet, so nothing is encrypted at rest.**
   `security.md` requires encryption or an entry here. This is the entry, and it stands until the
   first app stores a token — `docs/structure-decisions.md` keeps the question open.
