# accounts

A connected Instagram account and the token that speaks for it. This is the first app in the
project that stores anything, and what it stores is the most dangerous value in the codebase.

## Status

One model, migrated, with `selectors.py`, `services.py` and two management commands. No endpoints
and no serializers — nothing has asked for them.

## Models

- `InstagramAccount` — `instagram_id` is Meta's, a string, unique, and **not** the primary key: an
  account can be reconnected and a foreign key pointing at somebody else's identifier would make
  that a data migration. `access_token` is the long-lived token. `expires_at` is when Meta stops
  accepting it; `refreshed_at` is when we last replaced it, and it is what the 24-hour rule is
  measured against. `is_connected` false means every selector should treat the account as gone,
  with `disconnect_reason` saying which failure did it.

## The token is encrypted in the column

`fields.EncryptedTextField` encrypts on the way in and decrypts on the way out, so no service ever
handles ciphertext and no future writer can forget. Fernet, with
`INSTAGRAM_TOKEN_ENCRYPTION_KEY` from `.env`.

**An empty key raises rather than storing plaintext.** That is the whole point: the failure mode a
plain column would have is a database dump that hands over somebody's business account, and it
would be silent. A test reads the column with raw SQL and asserts the token is not in it.

The key lives in `.env` beside the database credentials, so this defends a stolen dump or a
backup — not an attacker who already has the server. `docs/security-debt.md` says so.

## The 60-day clock is the whole design

A long-lived token lasts about 60 days. It can be refreshed **only** while it is at least 24 hours
old and has not expired, and refreshing resets the 60 days. Miss the window and it is dead: no
recovery, no API call, a person has to reconnect the account by hand.

`account_list_due_for_refresh` is those two bounds as a query, narrowed by
`REFRESH_WINDOW_DAYS` — ten days before expiry. That number is the margin: with a daily cron, ten
days is ten chances to survive an outage, a bad deploy or a holiday. It is ours, not Meta's.

## Refresh either succeeds or says why the account is gone

`account_token_refresh` disconnects the account on `InstagramTokenInvalid` or
`InstagramPermissionDenied` — Meta will never accept that token again, so retrying it every day
until expiry is noise that hides the accounts still worth refreshing. It re-raises so the command
counts it as a failure.

A transient failure leaves `is_connected` alone. Tomorrow's run tries again.

## Running it

`connect_instagram_account <instagram_id> <short_lived_token>` exchanges and stores. It is the only
way a token enters the system; there is no OAuth endpoint yet.

`refresh_instagram_tokens` is the cron job. It prints `due N, refreshed N, failed N` and **exits
non-zero when anything failed**, because a non-zero exit and the cron log are the only signals cron
gives — a daily job that silently does nothing looks exactly like one that is not running.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file after finishing work here.
