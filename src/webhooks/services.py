from logging import getLogger

from django.conf import settings

from src.integrations.telegram.client import message_send
from src.integrations.telegram.exceptions import TelegramError
from src.webhooks.formatting import delivery_messages

logger = getLogger(__name__)


def instagram_delivery_forward(*, payload: dict) -> None:
    for text in delivery_messages(payload):
        try:
            message_send(chat_id=settings.TELEGRAM_DEBUG_CHAT_ID, text=text)
        except TelegramError as exc:
            logger.warning('instagram delivery not forwarded', extra={'reason': str(exc)})
            return
