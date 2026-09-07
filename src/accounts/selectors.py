from datetime import timedelta

from django.db.models import QuerySet
from django.utils.timezone import now

from src.accounts.constants import MINIMUM_TOKEN_AGE_HOURS, REFRESH_WINDOW_DAYS
from src.accounts.models import InstagramAccount


def account_list_due_for_refresh() -> QuerySet[InstagramAccount]:
    moment = now()

    return InstagramAccount.objects.filter(
        is_connected=True,
        expires_at__gt=moment,
        expires_at__lte=moment + timedelta(days=REFRESH_WINDOW_DAYS),
        refreshed_at__lte=moment - timedelta(hours=MINIMUM_TOKEN_AGE_HOURS),
    )
