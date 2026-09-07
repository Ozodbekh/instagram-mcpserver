from hashlib import sha256
from hmac import new
from json import dumps
from unittest.mock import patch

import pytest
from django.test import override_settings

WEBHOOK_URL = '/api/webhooks/instagram/'
APP_SECRET = 'an-app-secret-that-is-not-real'
VERIFY_TOKEN = 'a-verify-token-that-is-not-real'
CHAT_ID = '6694626582'

A_COMMENT = {
    'object': 'instagram',
    'entry': [
        {
            'id': '17841400000000000',
            'time': 1772000000,
            'changes': [
                {
                    'field': 'comments',
                    'value': {
                        'id': '17900000000000000',
                        'text': 'salom',
                        'from': {'id': '78000000000000000', 'username': 'someone'},
                        'media': {'id': '17800000000000000'},
                    },
                }
            ],
        }
    ],
}

A_DIRECT_MESSAGE = {
    'object': 'instagram',
    'entry': [
        {
            'id': '17841400000000000',
            'time': 1757250000000,
            'messaging': [
                {
                    'sender': {'id': '78000000000000000'},
                    'recipient': {'id': '17841400000000000'},
                    'timestamp': 1757250000000,
                    'message': {'mid': 'aWc6...', 'text': 'qalaysiz'},
                }
            ],
        }
    ],
}


def signed(payload, *, secret=APP_SECRET, body=None):
    raw = body if body is not None else dumps(payload).encode()
    digest = new(secret.encode(), raw, sha256).hexdigest()

    return raw, f'sha256={digest}'


@pytest.fixture(autouse=True)
def configured():
    with override_settings(
        INSTAGRAM_APP_SECRET=APP_SECRET,
        INSTAGRAM_WEBHOOK_VERIFY_TOKEN=VERIFY_TOKEN,
        TELEGRAM_BOT_TOKEN='000000:not-a-real-token',
        TELEGRAM_DEBUG_CHAT_ID=CHAT_ID,
    ):
        yield


@pytest.fixture(autouse=True)
def telegram():
    with patch('src.webhooks.services.message_send') as send:
        yield send
