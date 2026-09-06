from os import environ

environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
