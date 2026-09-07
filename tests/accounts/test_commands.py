from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.timezone import now

from src.accounts.models import InstagramAccount
from src.integrations.instagram.exceptions import InstagramTokenInvalid, InstagramUnavailable
from tests.accounts.conftest import AN_INSTAGRAM_ID, build_account

pytestmark = pytest.mark.django_db


def refresh():
    out = StringIO()
    call_command('refresh_instagram_tokens', stdout=out)

    return out.getvalue().strip()


def test_the_command_refreshes_only_what_is_due(issued):
    due = build_account(instagram_id='1', expires_at=now() + timedelta(days=3))
    build_account(instagram_id='2', expires_at=now() + timedelta(days=50))

    assert refresh() == 'due 1, refreshed 1, failed 0'

    due.refresh_from_db()
    assert due.access_token == 'a-fresh-token'


def test_the_command_says_so_and_exits_non_zero_when_a_refresh_fails(issued):
    token_refresh, _ = issued
    token_refresh.side_effect = InstagramUnavailable('token_refresh')
    build_account(expires_at=now() + timedelta(days=3))

    with pytest.raises(SystemExit):
        refresh()


def test_one_failure_does_not_stop_the_others(issued):
    token_refresh, _ = issued
    token_refresh.side_effect = [InstagramTokenInvalid('token_refresh'), token_refresh.return_value]
    build_account(instagram_id='1', expires_at=now() + timedelta(days=3))
    build_account(instagram_id='2', expires_at=now() + timedelta(days=4))

    with pytest.raises(SystemExit):
        refresh()

    assert InstagramAccount.objects.filter(is_connected=True).count() == 1


def test_nothing_due_is_a_clean_run(issued):
    build_account(expires_at=now() + timedelta(days=50))

    assert refresh() == 'due 0, refreshed 0, failed 0'


def test_the_connect_command_stores_the_account(issued):
    out = StringIO()

    call_command('connect_instagram_account', AN_INSTAGRAM_ID, 'a-short-lived-token', stdout=out)

    assert InstagramAccount.objects.get(instagram_id=AN_INSTAGRAM_ID).access_token == 'a-fresh-token'
    assert AN_INSTAGRAM_ID in out.getvalue()


def test_the_connect_command_reports_a_refusal_rather_than_a_traceback(issued):
    _, exchange = issued
    exchange.side_effect = InstagramTokenInvalid('token_exchange')

    with pytest.raises(CommandError):
        call_command('connect_instagram_account', AN_INSTAGRAM_ID, 'a-short-lived-token')
