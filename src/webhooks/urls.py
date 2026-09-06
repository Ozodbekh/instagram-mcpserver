from django.urls import path

from src.webhooks.views import InstagramWebhookView

urlpatterns = [
    path('instagram/', InstagramWebhookView.as_view(), name='instagram-webhook'),
]
