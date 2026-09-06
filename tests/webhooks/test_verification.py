import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from tests.webhooks.conftest import VERIFY_TOKEN, WEBHOOK_URL

A_CHALLENGE = '1158201444'


def verify(*, mode='subscribe', token=VERIFY_TOKEN, challenge=A_CHALLENGE):
    return APIClient().get(
        WEBHOOK_URL,
        {'hub.mode': mode, 'hub.verify_token': token, 'hub.challenge': challenge},
    )


def test_meta_gets_the_challenge_back_verbatim():
    response = verify()

    assert response.status_code == 200
    assert response.content.decode() == A_CHALLENGE
    assert response['Content-Type'].startswith('text/plain')


def test_a_wrong_verify_token_is_refused():
    response = verify(token='not-the-token')

    assert response.status_code == 403
    assert response.json() == {'code': 'verification_failed'}


def test_a_mode_other_than_subscribe_is_refused():
    assert verify(mode='unsubscribe').status_code == 403


def test_a_request_with_no_parameters_at_all_is_refused():
    assert APIClient().get(WEBHOOK_URL).status_code == 403


@override_settings(INSTAGRAM_WEBHOOK_VERIFY_TOKEN='')
@pytest.mark.parametrize('token', ['', 'anything'])
def test_an_unconfigured_verify_token_refuses_everything(token):
    assert verify(token=token).status_code == 403
