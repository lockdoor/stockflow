from django.test import TestCase

from tests.mixin import MixinSetupProduction

from inventory.models import MaterialReservation
from production.models import ProductionOrder, WIPStockMovement
from catalog.models import ItemSKU
from inventory.models import StockMovement, Stock, StockMovementItem

from tests.factories.inventory import StockMovementFactory, StockMovementItemFactory

class InProgressProductOrderTests(MixinSetupProduction, TestCase):
    """
        This test will check the following:
        1. First stock movement is created by referencing this production order
        2. Stock quantity is reduced
        3. Reserved quantity is reduced
        4. Material in WIP is increased
        5. Production order status is updated to IN_PROGRESS
        """
        
    catalog_categories_name = ['category_1', 'category_2', 'category_3']
    inventory_warehouses_name = ['warehouse_1']
    
    def setUp(self):
        super().setUp()
        
    def _get_stock_and_reservation(self, materials: list[ItemSKU], production_order: ProductionOrder):
        initial = {}
        for material in materials:
            material: ItemSKU
            if initial.get(material.id) is None:
                initial[material.id] = {}
            initial[material.id]['stock'] = Stock.get_total_stock(material, production_order.warehouse)
        reservations = MaterialReservation.get_all_product_reservation(production_order)
        for reservation in reservations:
            if initial.get(material.id) is None:
                initial[material.id] = {}
            initial[reservation.item_sku.id]['reserve'] = reservation.reserved_quantity
        return initial
        
    def test_environment_setup(self):
        self.assertEqual(len(self.catalog_categories), 3)
        for i in range(1, 4):
            self.assertIn(f'category_{i}', self.catalog_categories_name)
        
        # default warehouse number
        self.assertEqual(len(self.inventory_warehouses), 1)
        
        # default production order one per warehouse
        self.assertEqual(len(self.production_orders), 1)
        
        # default planned_quantity per production order
        self.assertEqual(self.production_planned_quantity, [10])
        
    def test_stockmovement_with_production_order(self):
        withdraw_quantity = 50
        production_order: ProductionOrder = self.production_orders[0]
        stock_movement: StockMovement = StockMovementFactory(
            warehouse=production_order.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=production_order.id,
            created_by=self.admin_user,
        )
        
        self.assertEqual(stock_movement.status, StockMovement.Status.DRAFT)
        
        materials = production_order.get_bom_material_items()
        for material in materials:
            StockMovementItemFactory(
                stock_movement=stock_movement, 
                item_sku=material, 
                quantity=withdraw_quantity,
                created_by=self.admin_user,
                movement_type=StockMovementItem.MovementType.OUT
            )
            
        # keep stock and reservation quantity before confirm stock_movement
        initial = self._get_stock_and_reservation(materials, production_order)
        
        # Confirm stock movement
        stock_movement.confirm(self.admin_user)
        
        # expect stock and reservation quantity decrese by withdraw_quantity
        present = self._get_stock_and_reservation(materials, production_order)
        self.assertEqual(len(initial), len(present))
        self.assertEqual(initial.keys(), present.keys())        
        for key in initial.keys():
            self.assertEqual(initial[key]['stock'] - withdraw_quantity, present[key]['stock'])
            self.assertEqual(initial[key]['reserve'] - withdraw_quantity, present[key]['reserve'])
        # refresh data
        stock_movement.refresh_from_db()
        production_order.refresh_from_db()
        self.assertEqual(stock_movement.status, StockMovement.Status.COMPLETED)
        self.assertEqual(production_order.status, ProductionOrder.Status.IN_PROGRESS)
        
        # WIP
        for material in materials:
            wip = WIPStockMovement.objects.filter(
                production_order=production_order,
                item_sku=material
            ).first()
            self.assertIsNotNone(wip)
            self.assertEqual(wip.quantity, withdraw_quantity)
