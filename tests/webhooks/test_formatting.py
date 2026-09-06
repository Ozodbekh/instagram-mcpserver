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
