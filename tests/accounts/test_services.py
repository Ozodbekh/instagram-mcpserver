from datetime import timedelta

import pytest
from django.db import connection
from django.utils.timezone import now

from src.accounts.models import InstagramAccount
from src.accounts.services import account_connect, account_disconnect, account_token_refresh
from src.integrations.instagram.exceptions import (
    InstagramPermissionDenied,
    InstagramTokenInvalid,
    InstagramUnavailable,
)
from tests.accounts.conftest import AN_INSTAGRAM_ID, SIXTY_DAYS, build_account

pytestmark = pytest.mark.django_db


def test_connecting_exchanges_the_short_lived_token_and_stores_the_long_lived_one(issued):
    _, exchange = issued

    account = account_connect(
        instagram_id=AN_INSTAGRAM_ID,
        short_lived_token='a-short-lived-token',
        username='sovchi.app',
    )

    assert exchange.call_args.kwargs == {'short_lived_token': 'a-short-lived-token'}
    assert account.access_token == 'a-fresh-token'
    assert account.expires_at > now() + timedelta(seconds=SIXTY_DAYS - 60)
    assert account.is_connected is True


def test_connecting_the_same_account_twice_keeps_one_row(issued):
    account_connect(instagram_id=AN_INSTAGRAM_ID, short_lived_token='one')
    account_connect(instagram_id=AN_INSTAGRAM_ID, short_lived_token='two')

    assert InstagramAccount.objects.count() == 1


def test_reconnecting_clears_a_previous_disconnection(issued):
    account = build_account(is_connected=False, disconnect_reason='token_refresh')

    account_connect(instagram_id=account.instagram_id, short_lived_token='one')
    account.refresh_from_db()

    assert account.is_connected is True
    assert account.disconnect_reason == ''


def test_the_column_holds_ciphertext_and_not_the_token(issued):
    account = build_account()

    with connection.cursor() as cursor:
        cursor.execute('select access_token from instagram_accounts where id = %s', [account.id])
        stored = cursor.fetchone()[0]

    assert stored != account.access_token
    assert 'IGAAQ' not in stored


def test_refreshing_moves_the_expiry_out(issued):
    refresh, _ = issued
    account = build_account(expires_at=now() + timedelta(days=3))

    account_token_refresh(account=account)
    account.refresh_from_db()

    assert refresh.call_args.kwargs == {'access_token': 'IGAAQ-a-long-lived-token-that-is-not-real'}
    assert account.access_token == 'a-fresh-token'
    assert account.expires_at > now() + timedelta(days=59)
    assert account.refreshed_at > now() - timedelta(minutes=1)


@pytest.mark.parametrize('failure', [InstagramTokenInvalid, InstagramPermissionDenied])
def test_a_token_meta_will_never_accept_again_disconnects_the_account(issued, failure):
    refresh, _ = issued
    refresh.side_effect = failure('token_refresh')
    account = build_account()

    with pytest.raises(failure):
        account_token_refresh(account=account)

    account.refresh_from_db()
    assert account.is_connected is False
    assert account.disconnect_reason == 'token_refresh'


def test_a_transient_failure_leaves_the_account_connected(issued):
    refresh, _ = issued
    refresh.side_effect = InstagramUnavailable('token_refresh')
    account = build_account()

    with pytest.raises(InstagramUnavailable):
        account_token_refresh(account=account)

    account.refresh_from_db()
    assert account.is_connected is True


def test_disconnecting_records_a_bounded_reason():
    account = build_account()

    account_disconnect(account=account, reason='x' * 500)
    account.refresh_from_db()

    assert account.is_connected is False
    assert len(account.disconnect_reason) == 64
