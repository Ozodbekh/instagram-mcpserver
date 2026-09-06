from logging import getLogger

from django.conf import settings
from requests import RequestException, post

from src.integrations.telegram.constants import (
    API_BASE_URL,
    CONNECT_TIMEOUT_SECONDS,
    MESSAGE_MAX_LENGTH,
    READ_TIMEOUT_SECONDS,
    SEND_MESSAGE_PATH,
    TRUNCATION_MARKER,
)
from src.integrations.telegram.exceptions import (
    TelegramNotConfigured,
    TelegramRefused,
    TelegramUnavailable,
)

logger = getLogger(__name__)


def message_send(*, chat_id: str, text: str) -> None:
    token = settings.TELEGRAM_BOT_TOKEN

    if not token:
        raise TelegramNotConfigured('bot_token_missing')

    if not chat_id:
        raise TelegramNotConfigured('chat_id_missing')

    url = API_BASE_URL + SEND_MESSAGE_PATH.format(token=token)
    body = {'chat_id': chat_id, 'text': fit_to_message_limit(text)}

    try:
        response = post(
            url,
            json=body,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
        )
    except RequestException as exc:
        raise TelegramUnavailable('unreachable') from exc

    if response.status_code != 200:
        logger.warning('telegram refused a message', extra={'status': response.status_code})
        raise TelegramRefused('refused')


def fit_to_message_limit(text: str) -> str:
    if len(text) <= MESSAGE_MAX_LENGTH:
        return text

    return text[: MESSAGE_MAX_LENGTH - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER
