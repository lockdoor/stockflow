from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random

from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.stock import Stock
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM


class Command(BaseCommand):
    help = 'Seed comprehensive inventory data with warehouses, items, stock movements and confirmations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-confirm',
            action='store_true',
            help='Skip automatic confirmation of stock movements',
        )
        parser.add_argument(
            '--items-count',
            type=int,
            default=10,
            help='Number of items to create (default: 10)',
        )
        parser.add_argument(
            '--movements-count',
            type=int,
            default=5,
            help='Number of stock movements per warehouse (default: 5)',
        )

    def handle(self, *args, **options):
        skip_confirm = options['skip_confirm']
        items_count = options['items_count']
        movements_count = options['movements_count']
        
        self.stdout.write("🚀 Starting comprehensive inventory seeding...")
        
        # Get or create superuser
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@stockflow.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('✅ Created superuser'))
        
        # 1. Create warehouses
        warehouses = self._create_warehouses(user)
        
        # 2. Create categories and items
        items = self._create_items_and_skus(user, items_count)
        
        # 3. Create stock movements
        movements = self._create_stock_movements(warehouses, items, user, movements_count)
        
        # 4. Confirm movements (unless skipped)
        if not skip_confirm:
            self._confirm_movements(movements, user)
        
        # 5. Summary
        self._print_summary(warehouses, items, movements, skip_confirm)

    def _create_warehouses(self, user):
        """Create sample warehouses"""
        self.stdout.write("\n📦 Creating warehouses...")
        
        warehouses = []
        
        # Clear existing data first (in proper order due to foreign keys)
        Stock.objects.all().delete()
        StockMovement.objects.all().delete()
        StockMovementItem.objects.all().delete()
        Warehouse.objects.all().delete()
        
        warehouse_data = [
            {
                'name': 'Main Warehouse',
                'address': '123 Main St, Bangkok 10100',
                'code': 'MAIN01',
                'note': 'Central storage facility for primary inventory',
            },
            {
                'name': 'Secondary Warehouse',
                'address': '456 Secondary Rd, Bangkok 10200',
                'code': 'SEC01',
                'note': 'Backup storage for overflow and specialized items',
            },
            {
                'name': 'Distribution Center',
                'address': '789 Distribution Ave, Bangkok 10300',
                'code': 'DIST01',
                'note': 'High-throughput distribution center for rapid fulfillment',
            }
        ]
        
        for data in warehouse_data:
            warehouse = Warehouse.objects.create(
                name=data['name'],
                address=data['address'],
                code=data['code'],
                note=data['note'],
                is_active=True,
                created_by=user,
                updated_by=user
            )
            warehouses.append(warehouse)
            self.stdout.write(f"   ✅ {warehouse.name} ({warehouse.code})")
        
        return warehouses

    def _create_items_and_skus(self, user, items_count):
        """Create sample items and SKUs"""
        self.stdout.write(f"\n📋 Creating {items_count} items with SKUs...")
        
        # Create categories first
        BOM.objects.all().delete()
        Category.objects.all().delete()
        categories = []
        
        category_data = [
            {'name': 'Electronics'},
            {'name': 'Office Supplies'},
            {'name': 'Food & Beverage'},
            {'name': 'Medical Supplies'},
            {'name': 'Industrial Tools'},
        ]
        
        for cat_data in category_data:
            category = Category.objects.create(
                name=cat_data['name'],
                is_active=True,
                created_by=user,
                updated_by=user
            )
            categories.append(category)
        
        # Create ItemSKUs
        ItemSKU.objects.all().delete()
        
        items = []
        item_templates = [
            {'name': 'Laptop Computer', 'category': 'Electronics', 'unit': 'PCS'},
            {'name': 'Office Chair', 'category': 'Office Supplies', 'unit': 'PCS'},
            {'name': 'Printing Paper A4', 'category': 'Office Supplies', 'unit': 'BOX'},
            {'name': 'Energy Drink', 'category': 'Food & Beverage', 'unit': 'CAN'},
            {'name': 'Surgical Mask', 'category': 'Medical Supplies', 'unit': 'BOX'},
            {'name': 'Hand Sanitizer', 'category': 'Medical Supplies', 'unit': 'BTL'},
            {'name': 'Electric Drill', 'category': 'Industrial Tools', 'unit': 'PCS'},
            {'name': 'Safety Helmet', 'category': 'Industrial Tools', 'unit': 'PCS'},
            {'name': 'Instant Noodles', 'category': 'Food & Beverage', 'unit': 'PKG'},
            {'name': 'USB Cable', 'category': 'Electronics', 'unit': 'PCS'},
        ]
        
        for i in range(items_count):
            template = item_templates[i % len(item_templates)]
            category = next(cat for cat in categories if cat.name == template['category'])
            
            # Create ItemSKU
            sku = ItemSKU.objects.create(
                sku_code=f"SKU-{i+1:03d}",
                name=f"{template['name']} - Model {i+1:03d}",
                unit=template['unit'],
                type=ItemSKU.Type.RAW,
                status=ItemSKU.Status.ACTIVE,
                category=category,
                created_by=user,
                updated_by=user
            )
            
            items.append(sku)
            
        self.stdout.write(f"   ✅ Created {len(items)} items with SKUs")
        return items

    def _create_stock_movements(self, warehouses, items, user, movements_count):
        """Create sample stock movements (one per warehouse due to business constraint)"""
        self.stdout.write(f"\n📊 Creating stock movements (1 per warehouse due to business rules)...")
        
        movements = []
        
        for warehouse in warehouses:
            # Only create one movement per warehouse due to unique constraint
            movement = StockMovement.objects.create(
                warehouse=warehouse,
                reference_type=StockMovement.ReferenceType.ADJUST,
                note=f"Initial stock adjustment for {warehouse.name}",
                status=StockMovement.Status.DRAFT,  # Start as DRAFT for confirmation
                created_by=user,
                updated_by=user
            )
            
            # Create StockMovementItems (use more items per movement since we only have one)
            items_in_movement = random.sample(items, random.randint(5, len(items)))
            
            for item_sku in items_in_movement:
                # Generate realistic quantities (always IN for initial stock)
                quantity = Decimal(str(random.randint(50, 200)))
                
                # Generate lot number and expiry date
                lot_number = f"LOT{random.randint(1000, 9999)}"
                
                # Expiry date: 30-365 days from now
                days_to_expire = random.randint(30, 365)
                expiry_date = date.today() + timedelta(days=days_to_expire)
                
                StockMovementItem.objects.create(
                    stock_movement=movement,
                    item_sku=item_sku,
                    quantity=quantity,
                    movement_type='IN',  # Always IN for initial seeding
                    lot_number=lot_number,
                    expiry_date=expiry_date,
                    note=f"Initial stock for {item_sku.sku_code}",
                    created_by=user,
                    updated_by=user
                )
            
            movements.append(movement)
                
        self.stdout.write(f"   ✅ Created {len(movements)} stock movements")
        return movements

    def _confirm_movements(self, movements, user):
        """Confirm stock movements to create actual stock records"""
        self.stdout.write(f"\n🔄 Confirming {len(movements)} stock movements...")
        
        confirmed_count = 0
        failed_count = 0
        
        for movement in movements:
            try:
                # Movement should still be in DRAFT status, so confirm() should work
                movement.confirm(user)
                confirmed_count += 1
                self.stdout.write(f"   ✅ Confirmed movement {movement.id}")
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Failed to confirm movement {movement.id}: {str(e)}")
                )
        
        self.stdout.write(f"   📊 Confirmation results: {confirmed_count} success, {failed_count} failed")

    def _print_summary(self, warehouses, items, movements, skip_confirm):
        """Print summary of created data"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🎉 SEEDING COMPLETED"))
        self.stdout.write("="*60)
        
        self.stdout.write(f"📦 Warehouses created: {len(warehouses)}")
        for warehouse in warehouses:
            self.stdout.write(f"   • {warehouse.name} ({warehouse.code})")
        
        self.stdout.write(f"\n📋 Items created: {len(items)}")
        categories = set(item.category.name for item in items if item.category)
        for category in categories:
            count = len([item for item in items if item.category and item.category.name == category])
            self.stdout.write(f"   • {category}: {count} items")
        
        self.stdout.write(f"\n📊 Stock movements created: {len(movements)}")
        # All movements are IN type for initial seeding
        self.stdout.write(f"   • IN movements: {len(movements)}")
        self.stdout.write(f"   • OUT movements: 0 (for initial seeding)")
        
        if not skip_confirm:
            completed_movements = [m for m in movements if m.status == StockMovement.Status.COMPLETED]
            self.stdout.write(f"   • Confirmed movements: {len(completed_movements)}")
        
        # Show some usage examples
        self.stdout.write(f"\n🔧 Next steps:")
        self.stdout.write("   • Check stock consistency:")
        self.stdout.write("     python manage.py check_stock_consistency")
        self.stdout.write("   • Test recovery mechanisms:")
        self.stdout.write("     python manage.py recover_stock_movements --dry-run")
        self.stdout.write("   • Access admin interface:")
        self.stdout.write("     http://localhost:8000/admin/")
        self.stdout.write("     Username: admin, Password: admin123")
        
        self.stdout.write(self.style.SUCCESS("\n✨ Ready for testing edge cases and recovery mechanisms!"))
