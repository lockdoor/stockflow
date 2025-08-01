"""
Stock Movement Recovery Management Command

Command to recover failed stock movements that were interrupted
due to system failures, power outages, or other issues.

Usage:
    python manage.py recover_stock_movements
    python manage.py recover_stock_movements --dry-run
    python manage.py recover_stock_movements --movement-id 123
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from inventory.models.stock_movement import StockMovement


class Command(BaseCommand):
    help = 'Recover failed stock movements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be recovered without actually doing it',
        )
        parser.add_argument(
            '--movement-id',
            type=int,
            help='Recover specific movement ID only',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='User ID to use for recovery operations (default: 1)',
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(id=options['user_id'])
        except User.DoesNotExist:
            raise CommandError(f"User with ID {options['user_id']} does not exist")

        dry_run = options['dry_run']
        movement_id = options['movement_id']

        if movement_id:
            # Recover specific movement
            try:
                movement = StockMovement.objects.get(id=movement_id)
                self._recover_single_movement(movement, user, dry_run)
            except StockMovement.DoesNotExist:
                raise CommandError(f"StockMovement with ID {movement_id} does not exist")
        else:
            # Recover all failed movements
            self._recover_all_failed_movements(user, dry_run)

    def _recover_single_movement(self, movement: StockMovement, user, dry_run):
        """Recover a single stock movement"""
        self.stdout.write(f"Processing movement ID: {movement.id}")
        self.stdout.write(f"  Status: {movement.status}")
        self.stdout.write(f"  Warehouse: {movement.warehouse.name}")
        self.stdout.write(f"  Created: {movement.created_at}")

        if not movement.can_be_recovered():
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠️  Movement cannot be recovered from status: {movement.status}"
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("  ✓ Would attempt recovery (dry run)")
            )
            return

        try:
            movement.recover(user)
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Successfully recovered movement {movement.id}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Failed to recover movement {movement.id}: {str(e)}")
            )

    def _recover_all_failed_movements(self, user, dry_run):
        """Recover all failed movements"""
        failed_movements = StockMovement.get_failed_movements()
        
        if not failed_movements:
            self.stdout.write(
                self.style.SUCCESS("✓ No failed movements found")
            )
            return

        self.stdout.write(f"Found {len(failed_movements)} failed movements:")
        
        for movement in failed_movements:
            self.stdout.write(f"\n  Movement ID: {movement.id}")
            self.stdout.write(f"    Status: {movement.status}")
            self.stdout.write(f"    Warehouse: {movement.warehouse.name}")
            self.stdout.write(f"    Created: {movement.created_at}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\n🔍 Dry run mode - would attempt to recover {len(failed_movements)} movements")
            )
            return

        self.stdout.write(f"\n🔄 Starting recovery process...")
        
        results = StockMovement.bulk_recover_failed_movements(user)
        
        self.stdout.write(f"\n📊 Recovery Results:")
        self.stdout.write(f"  Total processed: {results['total_processed']}")
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Successfully recovered: {results['recovered']}")
        )
        
        if results['still_failed'] > 0:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Still failed: {results['still_failed']}")
            )
            self.stdout.write(
                self.style.WARNING("    These movements may need manual intervention")
            )
        
        if results['recovered'] > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Recovery completed! {results['recovered']} movements recovered.")
            )
