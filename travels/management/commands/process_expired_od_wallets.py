from django.core.management.base import BaseCommand
from django.utils import timezone
from travels.models import ODWallet
from decimal import Decimal


class Command(BaseCommand):
    help = 'Process expired OD wallets: deduct remaining balance and deactivate'

    def handle(self, *args, **options):
        """Process all expired OD wallets"""
        now = timezone.now()
        expired_wallets = ODWallet.objects.filter(
            expires_at__lte=now,
            is_active=True
        )
        
        processed_count = 0
        for wallet in expired_wallets:
            if wallet.process_expiry():
                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Processed expired wallet for {wallet.user.email}: '
                        f'Used ₹{wallet.initial_balance - wallet.balance}, '
                        f'Remaining deducted, Balance: ₹{wallet.balance}'
                    )
                )
        
        if processed_count == 0:
            self.stdout.write(self.style.SUCCESS('No expired wallets to process.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully processed {processed_count} expired wallet(s).')
            )

