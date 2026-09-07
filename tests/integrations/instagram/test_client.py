from unittest.mock import patch

import pytest
from django.test import override_settings
from requests import ConnectTimeout

from src.integrations.instagram.client import token_exchange, token_refresh
from src.integrations.instagram.constants import (
    CONNECT_TIMEOUT_SECONDS,
    READ_TIMEOUT_SECONDS,
)
from src.integrations.instagram.exceptions import (
    InstagramPermissionDenied,
    InstagramRefused,
    InstagramThrottled,
    InstagramTokenInvalid,
    InstagramUnavailable,
)

AN_APP_SECRET = 'an-app-secret-that-is-not-real'
A_TOKEN = 'a-token-that-is-not-real'
SIXTY_DAYS = 5183944

METAS_OWN_SENTENCE = 'Error validating access token: Session has expired.'


@pytest.fixture
def called():
    with patch('src.integrations.instagram.client.get') as sent:
        sent.return_value.status_code = 200
        sent.return_value.json.return_value = {
            'access_token': 'a-fresh-token',
            'token_type': 'bearer',
            'expires_in': SIXTY_DAYS,
        }
        yield sent


def refused(*, code, status=400):
    body = {'error': {'message': METAS_OWN_SENTENCE, 'code': code, 'fbtrace_id': 'Axxxxxxx'}}
    with patch('src.integrations.instagram.client.get') as sent:
        sent.return_value.status_code = status
        sent.return_value.json.return_value = body
        yield sent


@override_settings(INSTAGRAM_APP_SECRET=AN_APP_SECRET)
def test_the_exchange_sends_the_documented_request(called):
    issued = token_exchange(short_lived_token=A_TOKEN)

    assert called.call_args.args[0] == 'https://graph.instagram.com/access_token'
    assert called.call_args.kwargs['params'] == {
        'grant_type': 'ig_exchange_token',
        'client_secret': AN_APP_SECRET,
        'access_token': A_TOKEN,
    }
    assert issued.access_token == 'a-fresh-token'
    assert issued.expires_in == SIXTY_DAYS


def test_the_refresh_sends_the_documented_request(called):
    token_refresh(access_token=A_TOKEN)

    assert called.call_args.args[0] == 'https://graph.instagram.com/refresh_access_token'
    assert called.call_args.kwargs['params'] == {
        'grant_type': 'ig_refresh_token',
        'access_token': A_TOKEN,
    }


def test_both_timeouts_are_explicit(called):
    token_refresh(access_token=A_TOKEN)

    assert called.call_args.kwargs['timeout'] == (CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS)


@pytest.mark.parametrize(
    ('code', 'expected'),
    [
        (190, InstagramTokenInvalid),
        (10, InstagramPermissionDenied),
        (200, InstagramPermissionDenied),
        (4, InstagramThrottled),
        (17, InstagramThrottled),
        (32, InstagramThrottled),
        (613, InstagramThrottled),
        (1234567, InstagramRefused),
    ],
)
def test_every_error_family_becomes_our_own_exception(code, expected):
    for _ in refused(code=code):
        with pytest.raises(expected):
            token_refresh(access_token=A_TOKEN)


def test_metas_own_sentence_never_reaches_the_caller():
    for _ in refused(code=190):
        with pytest.raises(InstagramTokenInvalid) as raised:
            token_refresh(access_token=A_TOKEN)

    assert METAS_OWN_SENTENCE not in str(raised.value)
    assert str(raised.value) == 'token_refresh'


def test_a_server_error_is_transient(called):
    called.return_value.status_code = 503

    with pytest.raises(InstagramUnavailable):
        token_refresh(access_token=A_TOKEN)


def test_a_network_failure_is_transient(called):
    called.side_effect = ConnectTimeout()

    with pytest.raises(InstagramUnavailable):
        token_refresh(access_token=A_TOKEN)


@pytest.mark.parametrize('body', [ValueError('not json'), 'a string', ['a list'], {'token_type': 'bearer'}])
def test_a_response_we_cannot_read_is_refused(called, body):
    if isinstance(body, Exception):
        called.return_value.json.side_effect = body
    else:
        called.return_value.json.return_value = body

    with pytest.raises(InstagramRefused):
        token_refresh(access_token=A_TOKEN)


def test_no_token_is_written_into_a_log_line(caplog):
    for _ in refused(code=190):
        with pytest.raises(InstagramTokenInvalid):
            token_refresh(access_token=A_TOKEN)

    assert caplog.records
    for record in caplog.records:
        assert A_TOKEN not in record.getMessage()
        assert A_TOKEN not in str(record.__dict__)
