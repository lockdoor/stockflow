from django.test import TestCase
from tests.factories.user import AdminFactory
from tests.factories.inventory import WarehouseFactory
from django.core.exceptions import ValidationError

from production.models.production_order import ProductionOrder
from production.models import ProductionOrderBOM
from tests.factories.catalog import ProductFactory
from tests.factories.production import ProductionOrderBOMFactory


class ProductionOrderTests(TestCase):
    
    def setUp(self):
        self.admin = AdminFactory()
        # self.product: ItemSKU = ProductFactory(
        #     created_by=self.admin,
        #     bom__bom_count=5
        #     )
        self.production_order = ProductionOrder.objects.create(
            warehouse=WarehouseFactory(created_by=self.admin),
            created_by=self.admin,
            updated_by=self.admin,
        )
        # self.warehouse
    
    def test_product_order_create(self):
        o = self.production_order
        self.assertEqual(o.warehouse.created_by, self.admin)
        self.assertEqual(o.created_by, self.admin)
        self.assertEqual(o.updated_by, self.admin)
        
        # default value
        self.assertEqual(o.status, ProductionOrder.Status.DRAFT)
        self.assertIsNone(o.started_at)
        self.assertIsNone(o.finished_at)
        self.assertEqual(o.note, "")

    def test_create_production_order_requires_draft_status(self):
        with self.assertRaises(ValidationError) as context:
            ProductionOrder.objects.create(
                status=ProductionOrder.Status.CREATED,
                warehouse=WarehouseFactory(created_by=self.admin),
                created_by=self.admin,
                updated_by=self.admin,
            )
        errors = context.exception.message_dict['__all__']
        self.assertIn("ProductionOrder initial status must be DRAFT.", errors)

    # def test_create_bom_requires_production_order_and_itemsku(self):
    #     pass

    # def test_stock_movement_reference_type_production_requires_production_order(self):
    #     pass

    def test_production_result_requires_warehouse(self):
        with self.assertRaises(ValidationError) as context:
            ProductionOrder.objects.create(
                status=ProductionOrder.Status.DRAFT,
                warehouse=None,
                created_by=self.admin,
                updated_by=self.admin,
            )
        self.assertIn('warehouse', context.exception.error_dict.keys())
        self.assertEqual('This field cannot be null.', context.exception.message_dict['warehouse'][0])

    def test_can_update_note_on_draft(self):
        self.production_order.note = "Updated note"
        self.production_order.save()
        self.assertEqual(self.production_order.note, "Updated note")

    # def test_production_loss_requires_reason_and_positive_quantity(self):
    #     pass

    # def test_audit_fields_are_set_on_create_and_update(self):
    #     pass

    # def test_version_increments_on_update(self):
    #     pass

    # def test_cannot_delete_production_order_with_bom_or_process(self):
    #     pass

    # def test_invalid_status_transition_raises_error(self):
    #     pass
    
class ProductionOrderBussinessTests(TestCase):
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.production_order = ProductionOrder.objects.create(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        
    def test_can_delete_draft(self):
        production_order_id=self.production_order.id
        ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=ProductFactory()
        )
        self.production_order.delete()
        self.assertFalse(ProductionOrder.objects.filter(id=production_order_id).exists())
        self.assertFalse(ProductionOrderBOM.objects.filter(production_order=production_order_id).exists())

    def test_can_not_change_draft_to_created_with_no_item(self):
        self.production_order.status = ProductionOrder.Status.CREATED
        with self.assertRaises(ValidationError) as context:
            self.production_order.save()
        errors = context.exception.messages
        self.assertIn('ProductionOrder must have at least one BOM item to change status from DRAFT to CREATED.', errors)
        
    def test_draft_can_change_created(self):
        ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=ProductFactory()
        )
        self.production_order.status = ProductionOrder.Status.CREATED
        self.production_order.save()
        
    def test_draft_can_change_created_only(self):
        ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=ProductFactory()
        )
        self.production_order.status = ProductionOrder.Status.CANCELLED
        with self.assertRaises(ValidationError) as context:
            self.production_order.save()
        errors = context.exception.messages
        self.assertIn('ProductionOrder must change from DRAFT to CREATED.', errors)

    def test_only_draft_can_delete(self):
        ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=ProductFactory()
        )
        self.production_order.status = ProductionOrder.Status.CREATED
        self.production_order.save()
        with self.assertRaises(ValidationError) as context:
            self.production_order.delete()
        errors = context.exception.messages
        self.assertIn('Only DRAFT production orders can be deleted.', errors)
        
    def test_can_not_change_warehouse_after_created(self):
        self.production_order.warehouse = WarehouseFactory()
        with self.assertRaises(ValidationError) as context:
            self.production_order.save()
        errors = context.exception.messages
        self.assertIn('Cannot change warehouse of an existing ProductionOrder.', errors)