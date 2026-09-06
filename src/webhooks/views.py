from json import JSONDecodeError, loads

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from rest_framework.views import APIView

from src.common.exceptions import DomainError
from src.webhooks.constants import (
    HUB_CHALLENGE_PARAM,
    HUB_MODE_PARAM,
    HUB_SUBSCRIBE_MODE,
    HUB_VERIFY_TOKEN_PARAM,
    INVALID_PAYLOAD,
    INVALID_SIGNATURE,
    SIGNATURE_HEADER,
    VERIFICATION_FAILED,
)
from src.webhooks.services import instagram_delivery_forward
from src.webhooks.signature import signature_matches, verify_token_matches


@extend_schema(exclude=True)
class InstagramWebhookView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        mode = request.query_params.get(HUB_MODE_PARAM, '')
        token = request.query_params.get(HUB_VERIFY_TOKEN_PARAM, '')

        if mode != HUB_SUBSCRIBE_MODE or not verify_token_matches(token=token):
            raise DomainError(VERIFICATION_FAILED, HTTP_403_FORBIDDEN)

        challenge = request.query_params.get(HUB_CHALLENGE_PARAM, '')

        return HttpResponse(challenge, content_type='text/plain; charset=utf-8')

    def post(self, request):
        raw_body = request.body

        if not signature_matches(raw_body=raw_body, header=request.headers.get(SIGNATURE_HEADER, '')):
            raise DomainError(INVALID_SIGNATURE, HTTP_403_FORBIDDEN)

        instagram_delivery_forward(payload=self.parsed(raw_body))

        return Response(status=HTTP_200_OK)

    def parsed(self, raw_body):
        try:
            payload = loads(raw_body)
        except (JSONDecodeError, UnicodeDecodeError) as exc:
            raise DomainError(INVALID_PAYLOAD, HTTP_400_BAD_REQUEST) from exc

        if not isinstance(payload, dict):
            raise DomainError(INVALID_PAYLOAD, HTTP_400_BAD_REQUEST)

        return payload
