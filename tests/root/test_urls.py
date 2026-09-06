from importlib import reload

import pytest
from django.test import override_settings
from django.urls import clear_url_caches
from rest_framework.test import APIClient

import root.urls


def load_urlconf(*, debug):
    with override_settings(DEBUG=debug):
        reload(root.urls)
    clear_url_caches()
    return [str(entry.pattern) for entry in root.urls.urlpatterns]


@pytest.fixture
def served_in_debug():
    load_urlconf(debug=True)
    yield
    load_urlconf(debug=False)


SCHEMA_PATTERNS = ['api/schema/', 'api/docs/']


def test_the_schema_paths_exist_only_under_debug():
    with_debug = load_urlconf(debug=True)
    without_debug = load_urlconf(debug=False)

    assert with_debug[-2:] == SCHEMA_PATTERNS
    assert not set(SCHEMA_PATTERNS) & set(without_debug)


def test_neither_is_reachable_with_debug_off():
    assert APIClient().get('/api/schema/').status_code == 404
    assert APIClient().get('/api/docs/').status_code == 404


def test_the_product_paths_are_routed_whatever_debug_says():
    assert load_urlconf(debug=True)[0] == ''
    assert load_urlconf(debug=False)[0] == ''


def test_the_schema_is_generated(served_in_debug):
    response = APIClient().get('/api/schema/')

    assert response.status_code == 200
    assert response['Content-Type'].startswith('application/vnd.oai.openapi')


def test_swagger_ui_is_served(served_in_debug):
    assert APIClient().get('/api/docs/').status_code == 200


def test_a_slashless_path_is_not_redirected(served_in_debug):
    assert APIClient().get('/api/schema').status_code == 404
