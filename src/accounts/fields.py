from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import TextField
from cryptography.fernet import Fernet, InvalidToken

from src.accounts.constants import ENCRYPTION_KEY_SETTING


class EncryptedTextField(TextField):
    def get_prep_value(self, value):
        if value in (None, ''):
            return value

        return _cipher().encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value in (None, ''):
            return value

        try:
            return _cipher().decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise ImproperlyConfigured(f'{ENCRYPTION_KEY_SETTING} does not decrypt this column') from exc


def _cipher():
    key = getattr(settings, ENCRYPTION_KEY_SETTING, '')

    if not key:
        raise ImproperlyConfigured(f'{ENCRYPTION_KEY_SETTING} is empty')

    return Fernet(key)
