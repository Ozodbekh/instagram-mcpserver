import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from src.accounts.fields import EncryptedTextField

A_KEY = Fernet.generate_key().decode()
ANOTHER_KEY = Fernet.generate_key().decode()
A_TOKEN = 'IGAAQ-a-token-that-is-not-real'


def stored(value, *, key=A_KEY):
    with override_settings(INSTAGRAM_TOKEN_ENCRYPTION_KEY=key):
        return EncryptedTextField().get_prep_value(value)


def loaded(value, *, key=A_KEY):
    with override_settings(INSTAGRAM_TOKEN_ENCRYPTION_KEY=key):
        return EncryptedTextField().from_db_value(value, None, None)


def test_a_token_survives_the_round_trip():
    assert loaded(stored(A_TOKEN)) == A_TOKEN


def test_what_reaches_the_column_is_not_the_token():
    assert A_TOKEN not in stored(A_TOKEN)


def test_the_same_token_encrypts_differently_every_time():
    assert stored(A_TOKEN) != stored(A_TOKEN)


@pytest.mark.parametrize('value', [None, ''])
def test_nothing_is_encrypted_when_there_is_nothing_to_encrypt(value):
    assert stored(value) == value
    assert loaded(value) == value


def test_an_unconfigured_key_refuses_rather_than_storing_plaintext():
    with pytest.raises(ImproperlyConfigured):
        stored(A_TOKEN, key='')


def test_the_wrong_key_refuses_rather_than_returning_rubbish():
    ciphertext = stored(A_TOKEN)

    with pytest.raises(ImproperlyConfigured):
        loaded(ciphertext, key=ANOTHER_KEY)
