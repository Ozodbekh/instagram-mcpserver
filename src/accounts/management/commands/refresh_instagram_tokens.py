from logging import getLogger

from django.core.management.base import BaseCommand

from src.accounts.selectors import account_list_due_for_refresh
from src.accounts.services import account_token_refresh
from src.integrations.instagram.exceptions import InstagramError

logger = getLogger(__name__)


class Command(BaseCommand):
    help = 'Refresh every Instagram token close enough to expiry to need it'

    def handle(self, *args, **options):
        due = list(account_list_due_for_refresh())
        failed = []

        for account in due:
            try:
                account_token_refresh(account=account)
            except InstagramError as exc:
                failed.append(account.instagram_id)
                logger.warning(
                    'instagram token not refreshed',
                    extra={'instagram_id': account.instagram_id, 'reason': str(exc)},
                )

        self.stdout.write(f'due {len(due)}, refreshed {len(due) - len(failed)}, failed {len(failed)}')

        if failed:
            raise SystemExit(1)
