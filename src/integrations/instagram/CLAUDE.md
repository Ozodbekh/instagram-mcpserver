# instagram

The Graph API client. Two calls today, both about tokens: exchange a short-lived one for a
long-lived one, and refresh a long-lived one before it dies.

## Which API this is

**Instagram API with Instagram Login — `graph.instagram.com`.** Not the Facebook Login variant on
`graph.facebook.com`, and the difference is not cosmetic: different hosts, different permission
names, different id spaces, and a different token model. Documentation written for the other one
looks almost right and fails at the third call — `docs/rules/instagram.md` opens with that warning.

It was chosen because it needs **no Facebook Page**. The account owner signs in with Instagram and
is done, where the Facebook Login flow requires every one of them to have a Page linked first. It
covers everything this project is for: publishing, insights, comments and messaging.

The cost is the token: it expires in 60 days and keeping it alive is our job, where a Facebook Page
access token does not expire. That is what `src/accounts/` exists to handle.

## The two calls

| | Path | Grant type |
|---|---|---|
| exchange | `/access_token` | `ig_exchange_token`, plus `client_secret` |
| refresh | `/refresh_access_token` | `ig_refresh_token` |

Both are `GET`, both answer `{access_token, token_type, expires_in}`, and both issue a token good
for about 60 days. `IssuedToken` is what leaves this package — Meta's JSON never does.

**A refresh is refused unless the token is at least 24 hours old and has not expired.** Both
bounds are Meta's, and `src/accounts/selectors.py` is where they turn into a query.

## The token travels in the query string

`docs/rules/instagram.md` forbids exactly this — a URL is logged by every proxy on the path. Meta's
endpoint takes no `Authorization` header for these two calls, so there is no version of this that
obeys the rule. It is `docs/security-debt.md` entry 4, and the mitigation is that nothing here logs
a URL: the failure log line carries the operation, Meta's code, subcode and trace id, and a test
asserts the token appears in no record.

## Errors are ours

`_translated` switches on Meta's numeric `code`, never on their message — the message is written
for their developers, is localized, and changes without notice. A test pins that Meta's sentence
never reaches a caller.

Four families, because each needs a different answer: an invalid token means the account must
reconnect, a permission failure means a scope was never granted, a rate limit means back off, and
anything else is refused. Only `InstagramUnavailable` is worth retrying.

## There is no retry here, on purpose

`docs/rules/instagram.md` asks for backoff on transient failures. The only caller is a daily cron
command working a **ten-day** window, so a transient failure today is retried tomorrow and nine
times after that. An in-process retry loop would add a second, worse schedule on top of the one
that already exists.

That changes with the first caller a person is waiting on.

## Notes

Current state only — no changelog, and nothing that does not exist yet. Git is the history.
Update this file after finishing work here.
