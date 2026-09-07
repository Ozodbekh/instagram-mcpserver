from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    Index,
    Model,
)

from src.accounts.constants import (
    DISCONNECT_REASON_MAX_LENGTH,
    INSTAGRAM_ID_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from src.accounts.fields import EncryptedTextField


class InstagramAccount(Model):
    instagram_id = CharField(max_length=INSTAGRAM_ID_MAX_LENGTH, unique=True)
    username = CharField(max_length=USERNAME_MAX_LENGTH, default='')
    access_token = EncryptedTextField()
    expires_at = DateTimeField()
    refreshed_at = DateTimeField()
    is_connected = BooleanField(default=True)
    disconnect_reason = CharField(max_length=DISCONNECT_REASON_MAX_LENGTH, default='')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instagram_accounts'
        ordering = ('instagram_id',)
        indexes = (Index(fields=('is_connected', 'expires_at'), name='account_refresh_due_idx'),)
