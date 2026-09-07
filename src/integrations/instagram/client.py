from dataclasses import dataclass
from logging import getLogger

from django.conf import settings
from requests import RequestException, get

from src.integrations.instagram.constants import (
    API_BASE_URL,
    CONNECT_TIMEOUT_SECONDS,
    EXCHANGE_GRANT_TYPE,
    EXCHANGE_PATH,
    INVALID_TOKEN_CODES,
    PERMISSION_CODES,
    RATE_LIMIT_CODES,
    READ_TIMEOUT_SECONDS,
    REFRESH_GRANT_TYPE,
    REFRESH_PATH,
)
from src.integrations.instagram.exceptions import (
    InstagramPermissionDenied,
    InstagramRefused,
    InstagramThrottled,
    InstagramTokenInvalid,
    InstagramUnavailable,
)

logger = getLogger(__name__)


@dataclass(frozen=True)
class IssuedToken:
    access_token: str
    expires_in: int


def token_exchange(*, short_lived_token: str) -> IssuedToken:
    return _issued(
        EXCHANGE_PATH,
        {
            'grant_type': EXCHANGE_GRANT_TYPE,
            'client_secret': settings.INSTAGRAM_APP_SECRET,
            'access_token': short_lived_token,
        },
        operation='token_exchange',
    )


def token_refresh(*, access_token: str) -> IssuedToken:
    return _issued(
        REFRESH_PATH,
        {'grant_type': REFRESH_GRANT_TYPE, 'access_token': access_token},
        operation='token_refresh',
    )


def _issued(path, params, *, operation):
    try:
        response = get(
            API_BASE_URL + path,
            params=params,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
        )
    except RequestException as exc:
        raise InstagramUnavailable(operation) from exc

    if response.status_code >= 500:
        raise InstagramUnavailable(operation)

    body = _decoded(response, operation=operation)

    if 'error' in body:
        raise _translated(body['error'], operation=operation)

    if 'access_token' not in body or 'expires_in' not in body:
        raise InstagramRefused(operation)

    return IssuedToken(access_token=body['access_token'], expires_in=int(body['expires_in']))


def _decoded(response, *, operation):
    try:
        body = response.json()
    except ValueError as exc:
        raise InstagramRefused(operation) from exc

    if not isinstance(body, dict):
        raise InstagramRefused(operation)

    return body


def _translated(error, *, operation):
    code = error.get('code')

    logger.warning(
        'instagram refused a call',
        extra={
            'operation': operation,
            'code': code,
            'subcode': error.get('error_subcode'),
            'trace_id': error.get('fbtrace_id'),
        },
    )

    if code in INVALID_TOKEN_CODES:
        return InstagramTokenInvalid(operation)
    if code in PERMISSION_CODES:
        return InstagramPermissionDenied(operation)
    if code in RATE_LIMIT_CODES:
        return InstagramThrottled(operation)

    return InstagramRefused(operation)
