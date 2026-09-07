from django.core.management.base import BaseCommand, CommandError

from src.accounts.services import account_connect
from src.integrations.instagram.exceptions import InstagramError


class Command(BaseCommand):
    help = 'Exchange a short-lived Instagram token for a long-lived one and store it'

    def add_arguments(self, parser):
        parser.add_argument('instagram_id')
        parser.add_argument('short_lived_token')
        parser.add_argument('--username', default='')

    def handle(self, *args, **options):
        try:
            account = account_connect(
                instagram_id=options['instagram_id'],
                short_lived_token=options['short_lived_token'],
                username=options['username'],
            )
        except InstagramError as exc:
            raise CommandError(f'instagram refused the exchange: {exc}') from exc

        self.stdout.write(f'connected {account.instagram_id}, expires {account.expires_at.isoformat()}')
