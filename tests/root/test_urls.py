from rest_framework.test import APIClient


def test_schema_is_generated():
    response = APIClient().get('/api/schema/')

    assert response.status_code == 200
    assert response['Content-Type'].startswith('application/vnd.oai.openapi')


def test_swagger_ui_is_served():
    response = APIClient().get('/api/docs/')

    assert response.status_code == 200


def test_a_slashless_path_is_not_redirected():
    response = APIClient().get('/api/schema')

    assert response.status_code == 404
