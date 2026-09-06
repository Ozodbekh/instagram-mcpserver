import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed, NotAuthenticated, Throttled, ValidationError
from rest_framework.status import HTTP_403_FORBIDDEN

from src.common.exceptions import DomainError, coded_exception_handler


def handled(exc):
    return coded_exception_handler(exc, {})


def test_a_domain_error_answers_with_its_own_code():
    response = handled(DomainError('invalid_signature', HTTP_403_FORBIDDEN))

    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.data == {'code': 'invalid_signature'}


def test_a_validation_error_names_the_fields():
    response = handled(ValidationError({'caption': ['max_length']}))

    assert response.data == {'code': 'validation_error', 'errors': {'caption': ['max_length']}}


@pytest.mark.parametrize(
    ('exc', 'code'),
    [
        (NotAuthenticated(), 'not_authenticated'),
        (MethodNotAllowed('PUT'), 'method_not_allowed'),
        (Throttled(), 'throttled'),
        (Http404(), 'not_found'),
        (DjangoPermissionDenied(), 'permission_denied'),
    ],
)
def test_every_standard_failure_maps_to_a_documented_code(exc, code):
    assert handled(exc).data == {'code': code}


def test_an_exception_drf_does_not_handle_is_left_to_django():
    assert handled(ValueError('boom')) is None


def test_no_sentence_survives_into_the_body():
    response = handled(NotAuthenticated('Authentication credentials were not provided.'))

    assert 'detail' not in response.data
    assert response.data == {'code': 'not_authenticated'}
