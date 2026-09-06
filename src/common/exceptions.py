from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

from src.common.constants import UNKNOWN_ERROR, VALIDATION_ERROR


class DomainError(APIException):
    def __init__(self, code, status_code):
        self.status_code = status_code
        super().__init__(detail=code)


def coded_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.data = {'code': VALIDATION_ERROR, 'errors': exc.detail}
        return response

    response.data = {'code': error_code(exc)}
    return response


def error_code(exc):
    if isinstance(exc, DomainError):
        return str(exc.detail)
    if isinstance(exc, Http404):
        return 'not_found'
    if isinstance(exc, DjangoPermissionDenied):
        return 'permission_denied'
    return getattr(exc, 'default_code', UNKNOWN_ERROR)
