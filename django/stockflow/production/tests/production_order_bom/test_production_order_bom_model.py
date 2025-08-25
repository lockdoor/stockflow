from django.test import TestCase

from common.mixins.validatable import ValidationError
from tests.factories.user import AdminFactory
from tests.factories.production import ProductionOrderFactory
from tests.factories.catalog import ProductFactory

from production.models import ProductionOrderBOM
from production.models import ProductionOrder

class ProductionOrderBOMTests(TestCase):
    def setUp(self):
        self.admin_user = AdminFactory()
        self.production_order = ProductionOrderFactory(
            created_by=self.admin_user, 
            warehouse__created_by=self.admin_user)
        self.product_1 = ProductFactory(created_by=self.admin_user)
        self.product_2 = ProductFactory(created_by=self.admin_user)
        
    def test_production_order_bom_creation(self):        
        bom = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product_1,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # required
        self.assertEqual(bom.production_order, self.production_order)
        self.assertEqual(bom.item_sku, self.product_1)
        self.assertEqual(bom.planned_quantity, 10)
        self.assertEqual(bom.created_by, self.admin_user)
        self.assertEqual(bom.updated_by, self.admin_user)

        # optional
        self.assertEqual(bom.note, '')

    def test_production_order_can_have_many_bom(self):
        bom1 = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product_1,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        bom2 = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product_2,
            planned_quantity=5,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

        self.assertEqual(self.production_order.boms.count(), 2)
        self.assertIn(bom1, self.production_order.boms.all())
        self.assertIn(bom2, self.production_order.boms.all())

    def test_bom_unique_constraint(self):
        ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product_1,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

        with self.assertRaises(ValidationError):
            ProductionOrderBOM.objects.create(
                production_order=self.production_order,
                item_sku=self.product_1,
                planned_quantity=5,
                created_by=self.admin_user,
                updated_by=self.admin_user
            )

        # self.assertIn("UNIQUE constraint failed", str(context.exception))
        
class ProductionOrderBOMBussinessTests(TestCase):
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.production_order = ProductionOrderFactory(
            created_by=self.admin_user, 
            warehouse__created_by=self.admin_user)
        self.product = ProductFactory(created_by=self.admin_user)
    
    def test_can_update_planned_quantity_when_status_draft(self):
        bom = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Update planned quantity
        bom.planned_quantity = 15
        bom.save()
        
        self.assertEqual(bom.planned_quantity, 15)
        

    def test_cannot_update_planned_quantity_when_status_is_not_draft(self):
        bom = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

        # Simulate changing the status to 'confirmed'
        self.production_order.status = ProductionOrder.Status.CREATED

        # Attempt to update planned quantity
        bom.planned_quantity = 15
        with self.assertRaises(ValidationError) as context:
            bom.save()

        errors = context.exception.messages

        self.assertIn('ProductionOrderBOM can only be updated when the production order status is DRAFT.', errors)
 