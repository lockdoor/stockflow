"""
Stock Consistency Check Management Command

Command to check for data inconsistencies between StockMovement and Stock tables.
Helps identify problems that may have occurred due to system failures.

Usage:
    python manage.py check_stock_consistency
    python manage.py check_stock_consistency --fix
    python manage.py check_stock_consistency --warehouse-id 1
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum, Q
from decimal import Decimal
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.stock import Stock
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU


class Command(BaseCommand):
    help = 'Check stock consistency and identify issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix identified issues',
        )
        parser.add_argument(
            '--warehouse-id',
            type=int,
            help='Check specific warehouse only',
        )

    def handle(self, *args, **options):
        fix_issues = options['fix']
        warehouse_id = options['warehouse_id']

        self.stdout.write("🔍 Starting stock consistency check...")

        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
                warehouses = [warehouse]
                self.stdout.write(f"   Checking warehouse: {warehouse.name}")
            except Warehouse.DoesNotExist:
                raise CommandError(f"Warehouse with ID {warehouse_id} does not exist")
        else:
            warehouses = Warehouse.objects.filter(is_active=True)
            self.stdout.write(f"   Checking {len(warehouses)} active warehouses")

        issues_found = 0

        for warehouse in warehouses:
            self.stdout.write(f"\n📦 Warehouse: {warehouse.name} ({warehouse.code})")
            warehouse_issues = self._check_warehouse_consistency(warehouse, fix_issues)
            issues_found += warehouse_issues

        if issues_found == 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ No consistency issues found!")
            )
        else:
            if fix_issues:
                self.stdout.write(
                    self.style.WARNING(f"\n⚠️  Found and attempted to fix {issues_found} issues")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"\n❌ Found {issues_found} consistency issues")
                )
                self.stdout.write("   Run with --fix to attempt repairs")

    def _check_warehouse_consistency(self, warehouse, fix_issues):
        """Check consistency for a specific warehouse"""
        issues = 0

        # Check 1: Orphaned stock movements (PROCESSING/FAILED status)
        orphaned_movements = StockMovement.objects.filter(
            warehouse=warehouse,
            status__in=[StockMovement.Status.PROCESSING, StockMovement.Status.FAILED]
        )

        if orphaned_movements.exists():
            count = orphaned_movements.count()
            issues += count
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  Found {count} movements in inconsistent state")
            )
            
            for movement in orphaned_movements:
                self.stdout.write(f"      Movement {movement.id}: {movement.status}")
                
            if fix_issues:
                self.stdout.write("      → These need manual recovery via recover_stock_movements command")

        # Check 2: Stock balance mismatches
        items_in_warehouse = Stock.objects.filter(warehouse=warehouse).values_list('item_sku', flat=True).distinct()
        
        for item_sku_id in items_in_warehouse:
            item_sku = ItemSKU.objects.get(id=item_sku_id)
            balance_issues = self._check_item_balance(warehouse, item_sku, fix_issues)
            issues += balance_issues

        return issues

    def _check_item_balance(self, warehouse, item_sku, fix_issues):
        """Check balance consistency for specific item in warehouse"""
        # Calculate expected balance from completed movements
        completed_movements = StockMovement.objects.filter(
            warehouse=warehouse,
            status=StockMovement.Status.COMPLETED
        )

        expected_balance = Decimal('0.000')
        
        for movement in completed_movements:
            movement_items = StockMovementItem.objects.filter(
                stock_movement=movement,
                item_sku=item_sku
            )
            
            for item in movement_items:
                if item.movement_type == 'IN':
                    expected_balance += item.quantity
                elif item.movement_type == 'OUT':
                    expected_balance -= item.quantity

        # Get actual balance from stock records
        actual_balance = Stock.get_total_stock(item_sku, warehouse)

        # Check for discrepancy
        if abs(expected_balance - actual_balance) > Decimal('0.001'):  # Allow small rounding differences
            self.stdout.write(
                self.style.ERROR(
                    f"   ❌ Balance mismatch for {item_sku.sku_code}:"
                )
            )
            self.stdout.write(f"      Expected: {expected_balance}")
            self.stdout.write(f"      Actual:   {actual_balance}")
            self.stdout.write(f"      Difference: {actual_balance - expected_balance}")
            
            if fix_issues:
                self.stdout.write("      → Manual intervention required for balance correction")
            
            return 1

        return 0
