from datetime import timedelta

import pytest
from django.utils.timezone import now

from src.accounts.selectors import account_list_due_for_refresh
from tests.accounts.conftest import build_account

pytestmark = pytest.mark.django_db


def test_an_account_inside_the_window_is_due():
    account = build_account(expires_at=now() + timedelta(days=3))

    assert list(account_list_due_for_refresh()) == [account]


def test_an_account_with_two_months_left_is_not_due_yet():
    build_account(expires_at=now() + timedelta(days=59))

    assert not account_list_due_for_refresh().exists()


def test_a_token_younger_than_a_day_is_not_due_because_meta_would_refuse_it():
    build_account(expires_at=now() + timedelta(days=3), refreshed_at=now() - timedelta(hours=2))

    assert not account_list_due_for_refresh().exists()


def test_an_expired_token_is_not_due_because_it_can_no_longer_be_refreshed():
    build_account(expires_at=now() - timedelta(minutes=1))

    assert not account_list_due_for_refresh().exists()


def test_a_disconnected_account_is_left_alone():
    build_account(expires_at=now() + timedelta(days=3), is_connected=False)

    assert not account_list_due_for_refresh().exists()
