from datetime import timedelta
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.test import override_settings
from django.utils.timezone import now

from src.accounts.models import InstagramAccount
from src.integrations.instagram.client import IssuedToken

A_KEY = Fernet.generate_key().decode()
AN_INSTAGRAM_ID = '17841400000000000'
A_TOKEN = 'IGAAQ-a-long-lived-token-that-is-not-real'
SIXTY_DAYS = 5183944


@pytest.fixture(autouse=True)
def configured():
    with override_settings(
        INSTAGRAM_TOKEN_ENCRYPTION_KEY=A_KEY,
        INSTAGRAM_APP_SECRET='an-app-secret-that-is-not-real',
    ):
        yield


@pytest.fixture
def issued():
    with patch('src.accounts.services.token_refresh') as refresh, patch(
        'src.accounts.services.token_exchange'
    ) as exchange:
        token = IssuedToken(access_token='a-fresh-token', expires_in=SIXTY_DAYS)
        refresh.return_value = token
        exchange.return_value = token
        yield refresh, exchange


def build_account(**overrides):
    moment = now()
    fields = {
        'instagram_id': AN_INSTAGRAM_ID,
        'username': 'sovchi.app',
        'access_token': A_TOKEN,
        'expires_at': moment + timedelta(days=60),
        'refreshed_at': moment - timedelta(days=2),
    }

    return InstagramAccount.objects.create(**(fields | overrides))
