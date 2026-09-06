from asyncio import Future, run
from hashlib import sha256
from hmac import new
from json import dumps
from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import override_settings

from root.asgi import application
from root.conf import Env

APP_SECRET = 'an-app-secret-that-is-not-real'
VERIFY_TOKEN = 'a-verify-token-that-is-not-real'
WEBHOOK_PATH = '/api/webhooks/instagram/'


def call(*, method, query=b'', body=b'', headers=()):
    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': method,
        'scheme': 'http',
        'path': WEBHOOK_PATH,
        'raw_path': WEBHOOK_PATH.encode(),
        'query_string': query,
        'root_path': '',
        'headers': [(b'host', b'testserver'), *headers],
        'server': ('127.0.0.1', 8005),
        'client': ('127.0.0.1', 55555),
    }
    sent = []
    incoming = [{'type': 'http.request', 'body': body, 'more_body': False}]

    async def receive():
        if incoming:
            return incoming.pop(0)
        await Future()

    async def send(message):
        sent.append(message)

    run(application(scope, receive, send))

    return sent[0]['status'], b''.join(m.get('body', b'') for m in sent[1:])


def test_the_env_file_is_found_from_any_working_directory():
    assert Path(Env.model_config['env_file']).is_absolute()


@override_settings(INSTAGRAM_WEBHOOK_VERIFY_TOKEN=VERIFY_TOKEN, ALLOWED_HOSTS=['testserver'])
def test_the_asgi_entrypoint_serves_the_verification_challenge():
    status, body = call(
        method='GET',
        query=b'hub.mode=subscribe&hub.verify_token=' + VERIFY_TOKEN.encode() + b'&hub.challenge=1158201444',
    )

    assert status == 200
    assert body == b'1158201444'


@override_settings(INSTAGRAM_APP_SECRET=APP_SECRET, TELEGRAM_DEBUG_CHAT_ID='1', ALLOWED_HOSTS=['testserver'])
def test_the_asgi_entrypoint_serves_a_signed_delivery():
    payload = dumps({'object': 'instagram', 'entry': [{'id': '1', 'changes': []}]}).encode()
    digest = new(APP_SECRET.encode(), payload, sha256).hexdigest()

    with patch('src.webhooks.services.message_send'):
        status, _ = call(
            method='POST',
            body=payload,
            headers=[
                (b'content-type', b'application/json'),
                (b'x-hub-signature-256', f'sha256={digest}'.encode()),
            ],
        )

    assert status == 200


@pytest.mark.parametrize('header', [b'sha256=' + b'0' * 64, b''])
@override_settings(INSTAGRAM_APP_SECRET=APP_SECRET, ALLOWED_HOSTS=['testserver'])
def test_the_asgi_entrypoint_refuses_an_unsigned_delivery(header):
    status, _ = call(
        method='POST',
        body=b'{}',
        headers=[(b'content-type', b'application/json'), (b'x-hub-signature-256', header)],
    )

    assert status == 403
