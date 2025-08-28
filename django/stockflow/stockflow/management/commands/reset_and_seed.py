from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import random

# factory
from tests.factories.user import AdminFactory, UserFactory
from tests.factories.catalog import CategoryFactory, ItemFactory, ProductFactory
from tests.factories.inventory import WarehouseFactory, StockMovementFactory, StockMovementItemFactory
from tests.factories.production import ProductionOrderFactory, ProductionOrderBOMFactory

class Command(BaseCommand):
    help = 'Reset database and seed all initial data'
    admin = None
    user = None
    items = []
    products = []
    warehouses = []
    production_orders = []

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Starting reset and seed process..."))
        call_command('delete_db')

        self.stdout.write(self.style.NOTICE("Running migrations..."))
        call_command('makemigrations')
        call_command('migrate')

        self._seed_user()

        self._seed_catalog()
        
        self._seed_inventory()
    
        self._seed_production()
        
    def _seed_user(self):
        self.stdout.write(self.style.NOTICE("Seeding initial data..."))
        self.stdout.write(self.style.NOTICE("Seeding users..."))
        self.admin = AdminFactory(username='admin', email='admin@example.com', password='admin123')
        self.user = UserFactory(username='user', email='user@example.com', password='user123')
        self.stdout.write(self.style.SUCCESS("Created users successfully."))

    def _seed_catalog(self):
        self.stdout.write(self.style.NOTICE("Seeding Catalog."))
        self.stdout.write(self.style.NOTICE("Seeding Category."))
        categories = ['Electronics', 'Clothing', 'Books']
        categories_record = []
        for category in categories:
            categories_record.append(CategoryFactory(name=category, created_by=self.admin))
        self.stdout.write(self.style.SUCCESS(f"Created categories {[category.name for category in categories_record]} successfully."))
        self.stdout.write(self.style.NOTICE("Seeding Items."))
        for i in range(1, 21):
            self.items.append(ItemFactory(name=f"Item {i}", created_by=self.user, category=categories_record[i % 3]))
        self.stdout.write(self.style.SUCCESS(f"Created items {[item.name for item in self.items]} successfully."))
        self.stdout.write(self.style.NOTICE("Seeding Products."))
        # products = []
        for i in range(1, 6):
            number_of_items = random.randint(2, 5)
            bom_items = random.sample(self.items, number_of_items)
            product = ProductFactory(name=f"Product {i}", created_by=self.user, category=categories_record[i % 3], bom=bom_items)
            self.products.append(product)
            self.stdout.write(self.style.SUCCESS(product.__repr__()))
        self.stdout.write(self.style.SUCCESS(f"Created Catalog successfully."))

    def _seed_inventory(self):
        self.stdout.write(self.style.NOTICE("Seeding Inventory."))
        warehouses = ['Main Warehouse', 'Secondary Warehouse']
        for warehouse in warehouses:
            self.warehouses.append(WarehouseFactory(name=warehouse, created_by=self.admin))
        self.stdout.write(self.style.SUCCESS(f"Created warehouses {[warehouse.name for warehouse in self.warehouses]} successfully."))

        self.stdout.write(self.style.NOTICE("Seeding Stock movement."))
        for warehouse in self.warehouses:
            # for _ in range(5):
            stock_movement = StockMovementFactory(
                warehouse=warehouse,
                created_by=self.admin
            )
            # Create stock movement items type IN
            for item in self.items:
                StockMovementItemFactory(
                    stock_movement=stock_movement, 
                    item_sku=item, 
                    quantity=random.randint(100, 1000),
                    created_by=self.admin
                )
            stock_movement.confirm(self.admin)
            self.stdout.write(self.style.NOTICE(stock_movement.__repr__()))

    def _seed_production(self):
        self.stdout.write(self.style.NOTICE("Seeding Production."))
        for warehouse in self.warehouses:
            production_order = ProductionOrderFactory(
                warehouse=warehouse,
                created_by=self.admin
            )
            self.production_orders.append(production_order)
            ProductionOrderBOMFactory(
                production_order=production_order,
                item_sku=self.products[0],
                planned_quantity=10,
                created_by=self.admin
            )
            production_order.created_production_order(self.admin)

        for production_order in self.production_orders:
            self.stdout.write(self.style.SUCCESS(production_order.__repr__()))