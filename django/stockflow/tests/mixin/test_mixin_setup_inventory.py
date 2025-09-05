from django.test import TestCase
import random

from . import MixinSetupCatalog
from ..factories.inventory import WarehouseFactory, StockMovementFactory, StockMovementItemFactory
from inventory.models import Warehouse, StockMovement
from catalog.models import ItemSKU

class MixinSetupInventory(MixinSetupCatalog):
    
    inventory_warehouses_name: list[str] = ['Main Warehouse', 'Secondary Warehouse']
    inventory_warehouses: list[Warehouse] = []
    inventory_stockmovements: list[StockMovement] = []
    inventory_stockmovement_number = 1
    inventory_stockmovement_item_min_quantity = 100
    inventory_stockmovement_item_max_quantity = 1000

    def setUp(self):
        super().setUp()
        # Set up additional test data for inventory tests
        for warehouse in self.inventory_warehouses_name:
            self.inventory_warehouses.append(
                WarehouseFactory(name=warehouse, created_by=self.admin_user))

        for warehouse in self.inventory_warehouses:
            for _ in range(self.inventory_stockmovement_number):
                stock_movement: StockMovement = StockMovementFactory(
                    warehouse=warehouse,
                    created_by=self.admin_user
                )
                # Create stock movement items type IN
                for item in self.catalog_items:
                    item: ItemSKU
                    StockMovementItemFactory(
                        stock_movement=stock_movement, 
                        item_sku=item, 
                        quantity=random.randint(
                            self.inventory_stockmovement_item_min_quantity, 
                            self.inventory_stockmovement_item_max_quantity),
                        created_by=self.admin_user
                    )
                stock_movement.confirm(self.admin_user)
                self.inventory_stockmovements.append(stock_movement)

class MyInventoryTests(MixinSetupInventory, TestCase):
    
    inventory_stockmovement_number = 2
    inventory_stockmovement_item_min_quantity = 200
    inventory_stockmovement_item_max_quantity = 500

    def test_inventory_setup(self):
        self.assertEqual(len(self.inventory_warehouses), len(self.inventory_warehouses_name))
        self.assertEqual(len(self.inventory_stockmovements), self.inventory_stockmovement_number * len(self.inventory_warehouses))
        for warehouse in self.inventory_warehouses:
            stock_movements = StockMovement.objects.filter(warehouse=warehouse)
            self.assertTrue(stock_movements.exists())
            for sm in stock_movements:
                self.assertEqual(sm.movement_items.count(), len(self.catalog_items))
                for item in sm.movement_items.all():
                    self.assertGreaterEqual(item.quantity, self.inventory_stockmovement_item_min_quantity)
                    self.assertLessEqual(item.quantity, self.inventory_stockmovement_item_max_quantity)
