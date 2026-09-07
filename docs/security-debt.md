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

## Accepted because the provider leaves no alternative

4. **The access token travels in the query string on both token calls.** `instagram.md` forbids it,
   and it is right: a URL is logged by every proxy on the path, and by Meta. Their
   `/access_token` and `/refresh_access_token` endpoints accept no `Authorization` header, so
   there is no version of these two calls that obeys the rule.

   **What bounds it:** the call is HTTPS, so the URL is not on the wire in clear; nothing in
   `src/integrations/instagram/` logs a URL, and a test asserts the token appears in no log
   record. It applies to these two endpoints only — every other Graph API call takes the header,
   and must use it.

## Partly closed

5. **Access tokens are encrypted at rest, with the key beside the database credentials.**
   `src/accounts/fields.py` encrypts the column with Fernet, so a database dump, a stolen backup or
   a read-only SQL leak hands over ciphertext. `INSTAGRAM_TOKEN_ENCRYPTION_KEY` lives in `.env` on
   the same host, so this does **not** defend against an attacker who already has the server.

   **What would close it:** a key held somewhere the application server is not — a KMS, or an
   operator-supplied key at start-up. Neither is worth it before there is more than one account.
