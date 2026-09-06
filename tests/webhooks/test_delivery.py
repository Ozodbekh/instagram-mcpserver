from json import dumps

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from src.integrations.telegram.exceptions import TelegramUnavailable
from tests.webhooks.conftest import A_COMMENT, A_DIRECT_MESSAGE, WEBHOOK_URL, signed


def deliver(raw, header):
    return APIClient().post(
        WEBHOOK_URL,
        data=raw,
        content_type='application/json',
        headers={'X-Hub-Signature-256': header},
    )


def test_a_signed_delivery_reaches_the_debug_chat(telegram):
    response = deliver(*signed(A_COMMENT))

    assert response.status_code == 200
    assert telegram.call_count == 1
    assert 'salom' in telegram.call_args.kwargs['text']


def test_a_direct_message_reaches_the_debug_chat(telegram):
    deliver(*signed(A_DIRECT_MESSAGE))

    text = telegram.call_args.kwargs['text']
    assert 'Instagram · messaging' in text
    assert 'qalaysiz' in text


def test_a_wrong_signature_is_refused_and_forwards_nothing(telegram):
    raw, _ = signed(A_COMMENT)
    response = deliver(raw, 'sha256=' + '0' * 64)

    assert response.status_code == 403
    assert response.json() == {'code': 'invalid_signature'}
    assert telegram.call_count == 0


def test_a_signature_from_another_secret_is_refused():
    assert deliver(*signed(A_COMMENT, secret='somebody-elses-secret')).status_code == 403


@pytest.mark.parametrize('header', ['', 'sha1=abc', 'abc'])
def test_a_missing_or_malformed_signature_header_is_refused(header):
    raw, _ = signed(A_COMMENT)

    assert deliver(raw, header).status_code == 403


@override_settings(INSTAGRAM_APP_SECRET='')
def test_an_unconfigured_app_secret_refuses_everything():
    assert deliver(*signed(A_COMMENT, secret='')).status_code == 403


def test_the_signature_covers_the_bytes_and_not_the_parsed_body():
    raw = dumps(A_COMMENT).encode()
    _, header = signed(A_COMMENT, body=dumps(A_COMMENT, indent=2).encode())

    assert deliver(raw, header).status_code == 403


def test_a_redelivery_is_forwarded_again(telegram):
    raw, header = signed(A_COMMENT)

    assert deliver(raw, header).status_code == 200
    assert deliver(raw, header).status_code == 200
    assert telegram.call_count == 2


@pytest.mark.parametrize('raw', [b'not json', b'[]', b'"a string"', b''])
def test_a_body_that_is_not_a_json_object_is_refused(raw):
    _, header = signed(None, body=raw)
    response = deliver(raw, header)

    assert response.status_code == 400
    assert response.json() == {'code': 'invalid_payload'}


def test_an_unknown_event_shape_is_still_acknowledged_and_forwarded(telegram):
    payload = {'object': 'instagram', 'entry': [{'id': '1', 'time': 1772000000, 'wat': {'x': 1}}]}

    assert deliver(*signed(payload)).status_code == 200
    assert telegram.call_count == 1
    assert 'Instagram · unknown' in telegram.call_args.kwargs['text']


def test_a_telegram_failure_never_makes_meta_retry(telegram):
    telegram.side_effect = TelegramUnavailable('unreachable')

    assert deliver(*signed(A_COMMENT)).status_code == 200


def test_a_telegram_failure_stops_the_rest_of_the_delivery(telegram):
    telegram.side_effect = TelegramUnavailable('unreachable')
    payload = {
        'entry': [
            {'id': '1', 'changes': [{'field': 'comments', 'value': {'a': 1}}]},
            {'id': '2', 'changes': [{'field': 'mentions', 'value': {'b': 2}}]},
            {'id': '3', 'changes': [{'field': 'comments', 'value': {'c': 3}}]},
        ]
    }

    assert deliver(*signed(payload)).status_code == 200
    assert telegram.call_count == 1
