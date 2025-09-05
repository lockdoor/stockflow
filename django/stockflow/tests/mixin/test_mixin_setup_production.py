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
        for warehouse in self.inventory_warehouses:
            products = random.sample(self.catalog_products, len(self.production_planned_quantity))
            for i, product in zip(self.production_planned_quantity, products):
                production_order: ProductionOrder = ProductionOrderFactory(
                    warehouse=warehouse,
                    created_by=self.admin_user
                )
                self.production_orders.append(production_order)

                ProductionOrderBOMFactory(
                    production_order=production_order,
                    item_sku=product,
                    planned_quantity=i,
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
