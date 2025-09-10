from django.test import TestCase
import random

from . import MixinSetupInventory
from production.models import ProductionOrder
from tests.factories.production import ProductionOrderFactory, ProductionOrderBOMFactory


class MixinSetupProduction(MixinSetupInventory):

    production_planned_quantity: list[int] = [10]
    production_orders: list[ProductionOrder] = []

    def setUp(self):
        super().setUp()
        # Set up additional test data for production tests
        if len(self.production_planned_quantity) > len(self.catalog_products):
            raise ValueError("production_planned_quantity ต้องไม่เกินจำนวน catalog_products ที่มี")
        
        for warehouse_idx, warehouse in enumerate(self.inventory_warehouses):
            # Use deterministic product selection instead of random.sample()
            # to avoid circular reference issues in parallel tests
            for quantity_idx, quantity in enumerate(self.production_planned_quantity):
                # Create fresh PRODUCT with BOM using existing raw materials
                from tests.factories.catalog import ProductFactory
                from catalog.models import ItemSKU
                
                # Use first few raw materials from catalog_items for BOM
                bom_components = self.catalog_items[:3] if len(self.catalog_items) >= 3 else self.catalog_items
                
                product = ProductFactory(
                    name=f"Prod-{warehouse_idx}-{quantity_idx}",
                    created_by=self.admin_user,
                    bom=bom_components  # Use existing raw materials as BOM
                )
                # ProductFactory automatically saves the product with BOM
                    
                production_order: ProductionOrder = ProductionOrderFactory(
                    warehouse=warehouse,
                    created_by=self.admin_user
                )
                self.production_orders.append(production_order)

                ProductionOrderBOMFactory(
                    production_order=production_order,
                    item_sku=product,
                    planned_quantity=quantity,
                    created_by=self.admin_user
                )
                production_order.created_production_order(self.admin_user)

class MyProductionSetupTests(MixinSetupProduction, TestCase):

    production_planned_quantity: list[int] = [10, 20]

    def test_production_setup(self):
        self.assertEqual(len(self.production_orders), len(self.inventory_warehouses) * len(self.production_planned_quantity))
        for production_order in self.production_orders:
            production_order: ProductionOrder
            self.assertEqual(production_order.bom_count, 1)
            self.assertEqual(production_order.created_by, self.admin_user)
            self.assertEqual(production_order.status, ProductionOrder.Status.CREATED)
