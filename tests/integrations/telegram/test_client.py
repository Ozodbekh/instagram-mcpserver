from unittest.mock import patch

import pytest
from django.test import override_settings
from requests import ConnectTimeout

from src.integrations.telegram.client import fit_to_message_limit, message_send
from src.integrations.telegram.constants import (
    CONNECT_TIMEOUT_SECONDS,
    MESSAGE_MAX_LENGTH,
    READ_TIMEOUT_SECONDS,
    TRUNCATION_MARKER,
)
from src.integrations.telegram.exceptions import (
    TelegramNotConfigured,
    TelegramRefused,
    TelegramUnavailable,
)

A_TOKEN = '000000:not-a-real-token'
A_CHAT_ID = '6694626582'


@pytest.fixture
def sent():
    with patch('src.integrations.telegram.client.post') as post:
        post.return_value.status_code = 200
        yield post


@override_settings(TELEGRAM_BOT_TOKEN=A_TOKEN)
def test_the_request_carries_the_token_the_chat_and_the_text(sent):
    message_send(chat_id=A_CHAT_ID, text='salom')

    url = sent.call_args.args[0]
    assert url == f'https://api.telegram.org/bot{A_TOKEN}/sendMessage'
    assert sent.call_args.kwargs['json'] == {'chat_id': A_CHAT_ID, 'text': 'salom'}


@override_settings(TELEGRAM_BOT_TOKEN=A_TOKEN)
def test_no_parse_mode_is_ever_sent(sent):
    message_send(chat_id=A_CHAT_ID, text='<b>not markup</b> _nor this_')

    assert 'parse_mode' not in sent.call_args.kwargs['json']


@override_settings(TELEGRAM_BOT_TOKEN=A_TOKEN)
def test_both_timeouts_are_explicit(sent):
    message_send(chat_id=A_CHAT_ID, text='salom')

    assert sent.call_args.kwargs['timeout'] == (CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS)


@override_settings(TELEGRAM_BOT_TOKEN='')
def test_an_unconfigured_bot_token_refuses_rather_than_calling(sent):
    with pytest.raises(TelegramNotConfigured):
        message_send(chat_id=A_CHAT_ID, text='salom')

    assert sent.call_count == 0


@override_settings(TELEGRAM_BOT_TOKEN=A_TOKEN)
def test_an_empty_chat_id_refuses_rather_than_guessing(sent):
    with pytest.raises(TelegramNotConfigured):
        message_send(chat_id='', text='salom')

    assert sent.call_count == 0


@override_settings(TELEGRAM_BOT_TOKEN=A_TOKEN)
def test_a_network_failure_becomes_our_own_exception(sent):
    sent.side_effect = ConnectTimeout()

    with pytest.raises(TelegramUnavailable):
        message_send(chat_id=A_CHAT_ID, text='salom')


@override_settings(TELEGRAM_BOT_TOKEN=A_TOKEN)
def test_a_refusal_becomes_our_own_exception(sent):
    sent.return_value.status_code = 400

    with pytest.raises(TelegramRefused):
        message_send(chat_id=A_CHAT_ID, text='salom')


def test_a_short_message_is_left_alone():
    assert fit_to_message_limit('salom') == 'salom'


def test_a_long_message_is_cut_to_the_limit_and_says_so():
    fitted = fit_to_message_limit('x' * (MESSAGE_MAX_LENGTH * 2))

    assert len(fitted) == MESSAGE_MAX_LENGTH
    assert fitted.endswith(TRUNCATION_MARKER)
