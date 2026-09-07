from datetime import timedelta
from logging import getLogger

from django.utils.timezone import now

from src.accounts.constants import DISCONNECT_REASON_MAX_LENGTH
from src.accounts.models import InstagramAccount
from src.integrations.instagram.client import IssuedToken, token_exchange, token_refresh
from src.integrations.instagram.exceptions import (
    InstagramPermissionDenied,
    InstagramTokenInvalid,
)

logger = getLogger(__name__)


def account_connect(*, instagram_id: str, short_lived_token: str, username: str = '') -> InstagramAccount:
    issued = token_exchange(short_lived_token=short_lived_token)

    account, _ = InstagramAccount.objects.update_or_create(
        instagram_id=instagram_id,
        defaults=_issued_fields(issued) | {
            'username': username,
            'is_connected': True,
            'disconnect_reason': '',
        },
    )

    logger.info('instagram account connected', extra={'instagram_id': instagram_id})

    return account


def account_token_refresh(*, account: InstagramAccount) -> InstagramAccount:
    try:
        issued = token_refresh(access_token=account.access_token)
    except (InstagramTokenInvalid, InstagramPermissionDenied) as exc:
        account_disconnect(account=account, reason=str(exc))
        raise

    for field, value in _issued_fields(issued).items():
        setattr(account, field, value)

    account.save(update_fields=('access_token', 'expires_at', 'refreshed_at', 'updated_at'))

    logger.info(
        'instagram token refreshed',
        extra={'instagram_id': account.instagram_id, 'expires_at': account.expires_at.isoformat()},
    )

    return account


def account_disconnect(*, account: InstagramAccount, reason: str) -> None:
    account.is_connected = False
    account.disconnect_reason = reason[:DISCONNECT_REASON_MAX_LENGTH]
    account.save(update_fields=('is_connected', 'disconnect_reason', 'updated_at'))

    logger.warning(
        'instagram account disconnected',
        extra={'instagram_id': account.instagram_id, 'reason': account.disconnect_reason},
    )


def _issued_fields(issued: IssuedToken) -> dict:
    moment = now()

    return {
        'access_token': issued.access_token,
        'expires_at': moment + timedelta(seconds=issued.expires_in),
        'refreshed_at': moment,
    }
