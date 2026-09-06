from django.conf import settings
from django.test import override_settings
from rest_framework.test import APIClient

from tests.root.test_urls import load_urlconf

AN_ALLOWED_ORIGIN = 'http://localhost:3000'


def preflight(origin, *, requested_header=None):
    headers = {'HTTP_ORIGIN': origin, 'HTTP_ACCESS_CONTROL_REQUEST_METHOD': 'GET'}
    if requested_header:
        headers['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'] = requested_header

    load_urlconf(debug=True)
    try:
        return APIClient().options('/api/schema/', **headers)
    finally:
        load_urlconf(debug=False)


def test_the_cors_middleware_runs_before_anything_that_answers():
    assert settings.MIDDLEWARE[0] == 'corsheaders.middleware.CorsMiddleware'


def test_authorization_is_listed_beside_the_wildcard():
    assert '*' in settings.CORS_ALLOW_HEADERS
    assert 'authorization' in settings.CORS_ALLOW_HEADERS


def test_credentials_stay_off():
    assert settings.CORS_ALLOW_CREDENTIALS is False


def test_cors_applies_to_the_api_only():
    assert settings.CORS_URLS_REGEX == r'^/api/.*$'


@override_settings(CORS_ALLOWED_ORIGINS=[AN_ALLOWED_ORIGIN])
def test_a_preflight_from_an_allowed_origin_is_answered():
    response = preflight(AN_ALLOWED_ORIGIN, requested_header='authorization')

    assert response.status_code == 200
    assert response['access-control-allow-origin'] == AN_ALLOWED_ORIGIN
    assert 'authorization' in response['access-control-allow-headers']


@override_settings(CORS_ALLOWED_ORIGINS=[AN_ALLOWED_ORIGIN])
def test_a_preflight_from_anywhere_else_gets_no_allow_origin():
    response = preflight('https://not-ours.example')

    assert 'access-control-allow-origin' not in response


@override_settings(CORS_ALLOWED_ORIGINS=[])
def test_no_configured_origin_means_no_cross_origin_access():
    response = preflight(AN_ALLOWED_ORIGIN)

    assert 'access-control-allow-origin' not in response
