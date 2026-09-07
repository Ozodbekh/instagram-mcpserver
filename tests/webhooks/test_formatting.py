from json import loads

import pytest

from src.webhooks.formatting import delivery_messages
from tests.webhooks.conftest import A_COMMENT, A_DIRECT_MESSAGE


def body_of(message):
    return loads(message.split('\n\n', 1)[1])


def test_a_comment_names_its_field_and_carries_the_value():
    message = delivery_messages(A_COMMENT)[0]

    assert message.startswith('Instagram · comments')
    assert 'account: 17841400000000000' in message
    assert body_of(message)['text'] == 'salom'


def test_the_entry_time_is_rendered_as_utc():
    assert 'time: 2026-02-25T06:13:20+00:00' in delivery_messages(A_COMMENT)[0]


def test_a_messaging_time_is_read_as_milliseconds():
    assert 'time: 2025-09-07T13:00:00+00:00' in delivery_messages(A_DIRECT_MESSAGE)[0]


@pytest.mark.parametrize('timestamp', [10 ** 30, -(10 ** 30), 'not a number', None, [1]])
def test_a_timestamp_that_cannot_be_rendered_costs_the_line_and_not_the_request(timestamp):
    message = delivery_messages({'entry': [{'id': '1', 'time': timestamp}]})[0]

    assert 'account: 1' in message
    assert 'time:' not in message


@pytest.mark.parametrize('entries', [{'entry': 'not a list'}, {'entry': 7}])
def test_an_entry_that_is_not_a_list_is_forwarded_whole(entries):
    assert len(delivery_messages(entries)) == 1


@pytest.mark.parametrize('key', ['changes', 'messaging'])
def test_a_shape_that_is_not_a_list_does_not_raise(key):
    assert len(delivery_messages({'entry': [{'id': '1', key: 'not a list'}]})) == 1


def test_a_messaging_entry_becomes_one_message_per_item():
    messages = delivery_messages(A_DIRECT_MESSAGE)

    assert len(messages) == 1
    assert messages[0].startswith('Instagram · messaging')
    assert body_of(messages[0])['message']['text'] == 'qalaysiz'


def test_every_event_in_a_delivery_gets_its_own_message():
    payload = {
        'entry': [
            {'id': '1', 'changes': [{'field': 'comments', 'value': {'a': 1}}, {'field': 'mentions', 'value': {'b': 2}}]},
            {'id': '2', 'messaging': [{'message': {'text': 'x'}}]},
        ]
    }

    assert len(delivery_messages(payload)) == 3


@pytest.mark.parametrize('payload', [{}, {'entry': []}, {'entry': ['not a dict']}])
def test_a_payload_with_nothing_recognisable_is_still_forwarded_whole(payload):
    assert len(delivery_messages(payload)) == 1


def test_non_ascii_text_survives():
    payload = {'entry': [{'id': '1', 'changes': [{'field': 'comments', 'value': {'text': 'Assalomu alaykum 🌙'}}]}]}

    assert '🌙' in delivery_messages(payload)[0]
