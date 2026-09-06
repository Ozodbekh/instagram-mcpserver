# Webhooks

Where Meta calls this service. **No client of ours calls these paths** — they are documented so the
contract with Meta is written down somewhere other than the code.

Both are on one path, and neither takes our authentication: Meta does not hold a token of ours. The
`GET` is authenticated by a shared verify token and the `POST` by a signature over the body.

Neither appears in the generated OpenAPI schema. A webhook has no serializer and no caller who
would read one.

## Verify a subscription

```
GET /api/webhooks/instagram/
```

Meta calls this once when the subscription is created or its callback URL changes, and expects the
challenge echoed back as plain text.

**Auth:** none · **Permission:** `AllowAny` · **Throttle:** none

**Query parameters**

| field | type | required | notes |
|---|---|---|---|
| `hub.mode` | string | yes | always `subscribe`; anything else is refused |
| `hub.verify_token` | string | yes | compared with `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` |
| `hub.challenge` | string | yes | echoed back verbatim on success |

**200 OK** — `text/plain`, the challenge and nothing else.

```
1158201444
```

**Errors**

| status | code | when |
|---|---|---|
| 403 | `verification_failed` | wrong verify token, a mode other than `subscribe`, or no verify token configured |

> An unconfigured `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` refuses every request rather than matching an
> empty one.

## Receive a delivery

```
POST /api/webhooks/instagram/
```

Forwards each event in the delivery to a Telegram chat. Nothing is stored. Answers `200` whether or
not the forward succeeded — any other status makes Meta redeliver.

**Auth:** none · **Permission:** `AllowAny` · **Throttle:** none

**Headers**

| header | required | notes |
|---|---|---|
| `X-Hub-Signature-256` | yes | `sha256=<hex>`, HMAC-SHA256 of the **raw body** with the app secret |

**Body** — whatever Meta sends. Two shapes arrive on this path:

```json
{
  "object": "instagram",
  "entry": [
    {
      "id": "17841400000000000",
      "time": 1772000000,
      "changes": [
        {
          "field": "comments",
          "value": {
            "id": "17900000000000000",
            "text": "salom",
            "from": {"id": "78000000000000000", "username": "someone"},
            "media": {"id": "17800000000000000"}
          }
        }
      ]
    }
  ]
}
```

```json
{
  "object": "instagram",
  "entry": [
    {
      "id": "17841400000000000",
      "time": 1772000001,
      "messaging": [
        {
          "sender": {"id": "78000000000000000"},
          "recipient": {"id": "17841400000000000"},
          "timestamp": 1772000001,
          "message": {"mid": "aWc6...", "text": "qalaysiz"}
        }
      ]
    }
  ]
}
```

A direct message arrives under `messaging`, not under `changes`. Which fields arrive at all is a
subscription setting in the Meta app dashboard.

**200 OK** — empty body.

**Errors**

| status | code | when |
|---|---|---|
| 400 | `invalid_payload` | the body is not a JSON object |
| 403 | `invalid_signature` | missing, malformed, or wrong `X-Hub-Signature-256`, or no app secret configured |

> The signature is verified over the exact bytes received, before anything parses them. A body that
> is re-serialised and re-signed will not match.

> **A redelivery is processed again.** Instagram webhooks carry no delivery id, nothing is stored
> here, and the only consequence is a duplicate message in the debug chat. A caller that later does
> something a duplicate would break gets idempotency in the same change.
