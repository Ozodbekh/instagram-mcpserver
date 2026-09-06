# telegram

Sends one message to one chat over the Bot API. It reads nothing back and it has no webhook: this
is an outbound notification channel, not a bot.

## Status

**It exists for one reason: watching what Instagram sends us while the product is being built.**
`src/webhooks/` forwards every delivery here so a person can read it on their phone instead of
tailing a log. That is a development aid with a real cost, and the cost is written down in
`docs/security-debt.md`.

## `message_send` is the whole surface

`message_send(chat_id=..., text=...)` posts to `sendMessage` and returns nothing. Failures are ours,
never `requests`': `TelegramNotConfigured` when the bot token or the chat id is empty,
`TelegramUnavailable` when the call did not complete, `TelegramRefused` when Telegram answered
anything but `200`.

`TELEGRAM_BOT_TOKEN` empty **refuses instead of calling** — an unconfigured deployment must not
build a URL with an empty token in it and send somebody's Instagram comments to whatever answers.
An empty `TELEGRAM_DEBUG_CHAT_ID` refuses for the same reason: there is no sensible default
destination for a private message.

## No `parse_mode`, ever

The text is a stranger's Instagram comment or direct message. With `parse_mode` set, a `<b>` or a
stray `_` in somebody's caption either breaks the send or renders as formatting the author chose —
`docs/rules/security.md` calls that text hostile, and plain text is what defuses it. A test pins the
absence, because the flag looks harmless and reads like an improvement.

## Two timeouts, no retry

Connect and read are separate numbers. A provider that accepts the connection and then thinks for
five minutes is exactly what a single timeout misses.

**There is no retry and that is deliberate.** The only caller is inside a webhook request that Meta
is waiting on, so a retry loop here becomes Meta's timeout and Meta's redelivery. A missed debug
message is recorded on the delivery row and the next one still arrives.

## Truncation

`fit_to_message_limit` cuts at Telegram's 4096-character limit and appends a marker, so a long
payload is short one message rather than zero.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file after finishing work here.
