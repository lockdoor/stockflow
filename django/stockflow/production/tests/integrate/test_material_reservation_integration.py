
from django.test import TestCase
from inventory.models import StockMovement, StockMovementItem, Stock, MaterialReservation
from production.models import ProductionOrder, ProductionOrderBOM
from catalog.models import ItemSKU

from tests.factories.user import AdminFactory
from tests.factories.production import ProductionOrderFactory, ProductionOrderBOMFactory
from tests.factories.catalog import ItemFactory, ProductFactory
from tests.factories.inventory import WarehouseFactory, StockMovementFactory, StockMovementItemFactory

ITEM_NUMBER = 3
ITEM_QUANTITY = 100

class MaterialReservationIntegrationTests(TestCase):
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.items: list[ItemSKU] = ItemFactory.create_batch(ITEM_NUMBER, type=ItemSKU.Type.RAW, created_by=self.admin_user)
        self.product: ItemSKU = ProductFactory(created_by=self.admin_user, bom=self.items)
        self.stock_movement: StockMovement = StockMovementFactory(warehouse=self.warehouse, created_by=self.admin_user)
        
        for item in self.items:
            StockMovementItemFactory(
                stock_movement=self.stock_movement, 
                item_sku=item, 
                created_by=self.admin_user, 
                quantity=ITEM_QUANTITY)

        # commit stock movement
        self.stock_movement.confirm(self.admin_user)
        
        self.order: ProductionOrder = ProductionOrderFactory(
            warehouse=self.warehouse,
            status=ProductionOrder.Status.DRAFT,
            created_by=self.admin_user
        )

    def test_environment_setup(self):
        self.assertIsNotNone(self.admin_user)
        self.assertIsNotNone(self.warehouse)
        self.assertGreater(len(self.items), 0)
        self.assertIsNotNone(self.product)
        self.assertEqual(self.product.bom_count, ITEM_NUMBER)
        self.assertIsNotNone(self.stock_movement)
        
        # this test is failed because stock movement is already confirmed
        self.assertFalse(self.stock_movement.can_be_confirmed()[0])
        self.assertEqual(self.stock_movement.get_total_items_count(), ITEM_NUMBER)
        items: list[StockMovementItem] = self.stock_movement.get_movement_items()
        self.assertEqual(len(items), ITEM_NUMBER)
        for item in items:
            self.assertIn(item.item_sku, self.items)
            self.assertGreaterEqual(item.quantity, ITEM_QUANTITY)

        # check stock availability after stock movement confirmation
        self.stock_movement.refresh_from_db()
        self.assertEqual(self.stock_movement.status, StockMovement.Status.COMPLETED)
        for item in self.items:
            result = Stock.get_total_stock(item, self.warehouse)
            self.assertEqual(result, ITEM_QUANTITY)
            
        # check production order
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ProductionOrder.Status.DRAFT)

    def test_create_production_order(self):
        ProductionOrderBOMFactory(
            production_order=self.order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

        # test draft again should error
        with self.assertRaises(ValueError) as context:
            self.order.draft_production_order(self.admin_user)
        self.assertEqual(str(context.exception), "Can only change status from CREATED to DRAFT.")

        self.order.created_production_order(self.admin_user)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ProductionOrder.Status.CREATED)
        self.assertEqual(self.order.bom_count, 1)
        
        # test create again should error
        with self.assertRaises(ValueError) as context:
            self.order.created_production_order(self.admin_user)
        self.assertEqual(str(context.exception), "Can only change status from DRAFT to CREATED.")
        
        # test draft again should success
        self.order.draft_production_order(self.admin_user)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ProductionOrder.Status.DRAFT)

    def test_create_production_order_recursive_bom(self):
        """Test creating production order with nested BOM structure and material reservations"""
        
        # Create nested BOM structure:
        # raw_materials -> intermediate_product -> final_product
        raw_materials = ItemFactory.create_batch(3, type=ItemSKU.Type.RAW, created_by=self.admin_user)
        intermediate_product = ProductFactory(created_by=self.admin_user, bom=raw_materials)
        
        # Create final product manually (not using factory)
        final_product = ItemSKU.objects.create(
            name='Final Product for Nested BOM Test',
            sku_code='FP-TEST-001',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status for new products
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create BOM components manually for final product
        from catalog.models import BOM
        # Add raw materials to final product BOM
        BOM.objects.create(
            parent_sku=final_product,
            component_sku=raw_materials[0],
            quantity=2,  # 2 units of first raw material
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        BOM.objects.create(
            parent_sku=final_product,
            component_sku=raw_materials[1],
            quantity=3,  # 3 units of second raw material
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        BOM.objects.create(
            parent_sku=final_product,
            component_sku=intermediate_product,
            quantity=1,  # 1 unit of intermediate product
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Ensure stock availability for all materials
        stock_movement_for_materials = StockMovementFactory(warehouse=self.warehouse, created_by=self.admin_user)
        for raw_material in raw_materials:
            StockMovementItemFactory(
                stock_movement=stock_movement_for_materials,
                item_sku=raw_material,
                created_by=self.admin_user,
                quantity=200  # Enough for production
            )
        
        # Also create stock for intermediate product
        StockMovementItemFactory(
            stock_movement=stock_movement_for_materials,
            item_sku=intermediate_product,
            created_by=self.admin_user,
            quantity=50
        )
        
        # Confirm stock movement to make materials available
        stock_movement_for_materials.confirm(self.admin_user)
        
        # Verify BOM structure
        bom_components = final_product.get_bom_components()
        self.assertEqual(len(bom_components), 3, "Final product should have 3 BOM components")
        
        # Calculate expected reservation quantities
        production_quantity = 10
        expected_reservations = {}
        for bom in bom_components:
            expected_quantity = bom.quantity * production_quantity
            expected_reservations[bom.component_sku.id] = expected_quantity
        
        # Create production order BOM
        production_bom = ProductionOrderBOMFactory(
            production_order=self.order,
            item_sku=final_product,
            planned_quantity=production_quantity,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Verify production order setup
        self.assertEqual(self.order.status, ProductionOrder.Status.DRAFT)
        self.assertEqual(self.order.bom_count, 1)
        
        # Move production order to CREATED status (this should trigger material reservations)
        self.order.created_production_order(self.admin_user)
        self.order.refresh_from_db()
        
        # Verify production order status change
        self.assertEqual(self.order.status, ProductionOrder.Status.CREATED)
        
        # Verify material reservations were created
        reservations = MaterialReservation.get_all_product_reservation(self.order)
        self.assertEqual(reservations.count(), 3, "Should have reservations for 3 components")
        
        # Verify specific material reservations
        for reservation in reservations:
            with self.subTest(item=reservation.item_sku.name):
                # Check basic reservation properties
                self.assertEqual(reservation.warehouse, self.warehouse)
                self.assertEqual(reservation.status, MaterialReservation.Status.RESERVED)
                self.assertEqual(reservation.reference_type, MaterialReservation.ReferenceType.PRODUCTION)
                self.assertEqual(reservation.reference_id, self.order.id)
                
                # Check reserved quantity matches expected calculation
                expected_qty = expected_reservations[reservation.item_sku.id]
                self.assertEqual(
                    reservation.reserved_quantity, 
                    expected_qty,
                    f"Reserved quantity for {reservation.item_sku.name} should be {expected_qty}"
                )
                
                # Verify stock availability
                available_stock = Stock.get_total_stock(reservation.item_sku, self.warehouse)
                self.assertGreaterEqual(
                    available_stock, 
                    reservation.reserved_quantity,
                    f"Not enough stock for {reservation.item_sku.name}"
                )
        
        # Verify that each expected component has a reservation
        expected_items = [raw_materials[0], raw_materials[1], intermediate_product]
        for expected_item in expected_items:
            self.assertTrue(
                reservations.filter(item_sku=expected_item).exists(),
                f"Missing reservation for {expected_item.name}"
            )
        
        # Test reservation cleanup when production order returns to DRAFT
        reservations_count_before = reservations.count()
        self.assertGreater(reservations_count_before, 0, "Should have reservations before cleanup")
        
        self.order.draft_production_order(self.admin_user)
        self.order.refresh_from_db()
        
        # Verify status change and reservation cleanup
        self.assertEqual(self.order.status, ProductionOrder.Status.DRAFT)
        remaining_reservations = MaterialReservation.get_all_product_reservation(self.order)
        self.assertEqual(remaining_reservations.count(), 0, "All reservations should be cleaned up")
        
        # Verify that reservations were actually deleted, not just hidden
        all_reservations_for_order = MaterialReservation.objects.filter(
            reference_type=MaterialReservation.ReferenceType.PRODUCTION,
            reference_id=self.order.id
        )
        self.assertEqual(all_reservations_for_order.count(), 0, "Reservations should be completely removed")

