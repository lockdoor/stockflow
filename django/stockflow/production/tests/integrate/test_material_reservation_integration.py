
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
        items = ItemFactory.create_batch(5, type=ItemSKU.Type.RAW, created_by=self.admin_user)
        product = ProductFactory(created_by=self.admin_user, bom=items)
        product_nested = ProductFactory(created_by=self.admin_user, bom=[items[0], items[1], product])
        
        boms = product_nested.get_bom_components()
        assert len(boms) == 3  # 2 raw items + 1 product
        planned_quantities = []
        for bom in boms:
            planned_quantities.append(bom.quantity * 5)  # multiply by 5 because we will create production order with quantity 5

        ProductionOrderBOMFactory(
            production_order=self.order,
            item_sku=product_nested,
            planned_quantity=5,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        self.order.created_production_order(self.admin_user)
        
        self.assertEqual(self.order.status, ProductionOrder.Status.CREATED)
        
        # MaterialReservation.__repr_with_product_order__(self.order)
        reservations = MaterialReservation.get_all_product_reservation(self.order)
        self.assertEqual(reservations.count(), 3)
        self.assertTrue(reservations.filter(item_sku=items[0]).exists())
        self.assertTrue(reservations.filter(item_sku=items[1]).exists())
        self.assertTrue(reservations.filter(item_sku=product).exists())
        for reservation in reservations:
            self.assertEqual(reservation.warehouse, self.warehouse)
            self.assertEqual(reservation.status, MaterialReservation.Status.RESERVED)
            self.assertGreater(reservation.reserved_quantity, 0)
            self.assertIn(reservation.reserved_quantity, planned_quantities)
            self.assertEqual(reservation.reference_type, MaterialReservation.ReferenceType.PRODUCTION)
            self.assertEqual(reservation.reference_id, self.order.id)

        # test set production to draft should delete reservations
        self.order.draft_production_order(self.admin_user)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ProductionOrder.Status.DRAFT)
        self.assertEqual(MaterialReservation.get_all_product_reservation(self.order).count(), 0)

