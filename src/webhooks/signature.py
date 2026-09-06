from hashlib import sha256
from hmac import compare_digest, new

from django.conf import settings

from src.webhooks.constants import SIGNATURE_PREFIX


def signature_matches(*, raw_body: bytes, header: str) -> bool:
    secret = settings.INSTAGRAM_APP_SECRET

    if not secret or not header.startswith(SIGNATURE_PREFIX):
        return False

    expected = new(secret.encode(), raw_body, sha256).hexdigest()

    return compare_digest(expected, header.removeprefix(SIGNATURE_PREFIX))


def verify_token_matches(*, token: str) -> bool:
    configured = settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN

    if not configured:
        return False

    return compare_digest(configured, token)
