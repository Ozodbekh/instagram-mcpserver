import pytest
from pydantic import ValidationError

from root.conf import SECRET_KEY_MIN_LENGTH, Env

A_VALID_KEY = 'k' * SECRET_KEY_MIN_LENGTH
REQUIRED = {
    'SECRET_KEY': A_VALID_KEY,
    'POSTGRES_DB': 'instagram_mcpserver',
    'POSTGRES_USER': 'instagram_mcpserver',
    'POSTGRES_PASSWORD': 'not-a-real-password',
}


def build(**overrides):
    return Env(_env_file=None, **{**REQUIRED, **overrides})


@pytest.mark.parametrize('raw', ['', 'k' * (SECRET_KEY_MIN_LENGTH - 1)])
def test_an_empty_or_short_secret_key_refuses_to_start(raw):
    with pytest.raises(ValidationError):
        build(SECRET_KEY=raw)


@pytest.mark.parametrize('key', sorted(REQUIRED))
def test_every_required_key_is_missing_rather_than_defaulted(key):
    supplied = {name: value for name, value in REQUIRED.items() if name != key}

    with pytest.raises(ValidationError):
        Env(_env_file=None, **supplied)


@pytest.mark.parametrize('key', ['SECRET_KEY', 'POSTGRES_PASSWORD'])
def test_a_secret_is_hidden_when_printed(key):
    env = build()

    assert REQUIRED[key] not in repr(env)
    assert getattr(env, key).get_secret_value() == REQUIRED[key]


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [
        ('', []),
        ('localhost', ['localhost']),
        ('localhost, 127.0.0.1 ', ['localhost', '127.0.0.1']),
    ],
)
def test_allowed_hosts_splits_on_commas(raw, expected):
    assert build(ALLOWED_HOSTS=raw).allowed_hosts == expected
