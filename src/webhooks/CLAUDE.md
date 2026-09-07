# webhooks

Where Meta calls us. One endpoint, `POST /api/webhooks/instagram/`, plus the `GET` on the same path
that Meta uses to verify the subscription.

## Status

**Not a Django app.** No models, no `apps.py`, not in `INSTALLED_APPS` — a delivery is verified,
formatted and forwarded, and nothing is stored. It is a view layer by `src/CLAUDE.md`'s test.

One endpoint, one service — the forward — and no selectors, because there is nothing to read.

## What Instagram actually sends

Two shapes arrive on the same path, and nothing in the payload announces which:

- **`entry[].changes[]`** — a `field` (`comments`, `mentions`, `live_comments`, `story_insights`)
  and a `value` object. This is the shape for anything about content.
- **`entry[].messaging[]`** — a direct message, a reaction, a postback. Same shape Messenger uses:
  `sender`, `recipient`, `timestamp`, `message`. **It is not under `changes`**, and code that only
  walks `changes` silently drops every DM.

`formatting.delivery_messages` walks both and falls back to forwarding the entry whole when it
recognises neither, because an unrecognised event is the one worth seeing.

**`entry.time` is in seconds under `changes` and in milliseconds under `messaging`.** That is
Meta's inconsistency, not ours, and it is invisible until a real direct message arrives: read as
seconds, a millisecond timestamp is the year 58654 and `datetime.fromtimestamp` raises. It cost a
`500` on every DM in production while comments kept working, which is exactly the shape a
unit mismatch takes. `_moment` switches on magnitude — past `MILLISECOND_THRESHOLD` no real event
time is in seconds.

Which fields arrive at all is a subscription setting in the Meta app dashboard, not something this
code controls.

## Verification is two different checks on one path

**`GET`** is Meta proving the subscription is ours. It carries `hub.mode`, `hub.verify_token` and
`hub.challenge`; we compare the token with `compare_digest` and echo the challenge as
`text/plain`. Echoing it as JSON would wrap it in quotes and Meta would reject the subscription —
that is why the `GET` returns `HttpResponse` and not DRF's `Response`.

**`POST`** is Meta proving the body is theirs. `X-Hub-Signature-256` is an HMAC-SHA256 of the
**raw bytes** with the app secret. `views.post` reads `request.body` before anything parses it, and
`signature.signature_matches` compares with `compare_digest`. Re-serialising the parsed body and
signing that produces a different digest — whitespace and key order change the bytes — and a test
pins it.

**An empty `INSTAGRAM_APP_SECRET` or `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` refuses everything.** Not
"accepts anything": an empty HMAC key still produces a digest anybody can compute, and
`compare_digest('', '')` is `True`. Both checks test for emptiness first.

## Nothing is stored, and there is no idempotency

`docs/rules/instagram.md` requires a webhook handler to be idempotent, keyed on a persisted event
id. This one is not, deliberately.

Meta redelivers on any non-`200` or timeout, so a redelivery sends the same Telegram message twice.
**A duplicate debug message costs nothing**, and the table that would prevent it costs a great
deal: Instagram webhooks carry no delivery id, so the key would have to be a hash of the body,
which means storing the body — every direct message and every comment a stranger wrote, kept
forever, in the one place `docs/rules/security.md` says such text must not accumulate.

The rule comes back the moment a handler does something a duplicate would break — a reply, a
counter, a state change. It has no such side effect today.

## Formatting never raises

Every value in the payload is a stranger's, and `docs/rules/security.md` calls that hostile. Here
that is not about injection but about **shape**: a list where an object was expected, a string
where a number was, a timestamp no calendar can hold. Each of those used to be a `500`, and a `500`
is worse than a wrong message — Meta redelivers on it, so one malformed field becomes a retry storm
and the payload is never seen at all, because nothing is stored.

So `delivery_messages` guards the shape at every branch and `_moment` returns `''` rather than
raising. There is deliberately **no blanket `except`** around the forward: the guards sit where
untrusted input is read, which is where they belong, and a genuine bug in our own code still
surfaces instead of being swallowed.

## Meta is answered `200` whatever happens next

A Telegram failure is logged and the endpoint still returns `200`. Anything else makes Meta
redeliver, and redelivering a message Telegram already refused fixes nothing while spending Meta's
retry budget.

The first failure also **stops the rest of the delivery**. If Telegram is unreachable, the second
and third message will not succeed either, and each attempt costs a timeout inside the request Meta
is waiting on.

## The forward is inline, and that is a deviation

`docs/rules/integrations.md` says to reply fast and do the work in the background. There is no
background worker yet — `docs/structure-decisions.md` keeps that open — so
`instagram_delivery_forward` calls Telegram inside the request, bounded by the client's own
timeouts. It moves to a task in the change that introduces one.

## The forwarder is temporary

Forwarding every delivery to one chat means **direct message contents and comment text leave this
system**. That is a deliberate development aid, logged as `docs/security-debt.md` entry 1 with what
removes it. It is not a feature and it does not survive into production.

## No throttle, on purpose

`docs/rules/security.md` makes a throttle mandatory on webhooks. DRF's throttle answers `429`, and
Meta treats any non-`200` as a failure and redelivers — so a throttle here converts a burst into a
larger burst. The signature check is what bounds the work an unsigned request can cause, and rate
limiting belongs in front of the application. `docs/security-debt.md` entry 2.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file after finishing work here.
