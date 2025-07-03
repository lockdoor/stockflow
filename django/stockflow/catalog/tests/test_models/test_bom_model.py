from django.test import TestCase
from catalog.models.item import ItemSKU, ItemSKUType
from catalog.models.bom import BOM
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class BOMModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester')
        self.parent = ItemSKU.objects.create(
            sku_code='P001',
            name='Product 1',
            unit='pcs',
            type=ItemSKUType.PRODUCT,
            status='ACTIVE',
            created_by=self.user,
            updated_by=self.user,
        )
        self.raw = ItemSKU.objects.create(
            sku_code='R001',
            name='Raw Material 1',
            unit='kg',
            type=ItemSKUType.RAW,
            status='ACTIVE',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_valid_bom_creation(self):
        bom = BOM(parent_sku=self.parent, component_sku=self.raw, quantity=1.5)
        bom.save()
        self.assertEqual(BOM.objects.count(), 1)

    def test_invalid_bom_with_raw_parent(self):
        bom = BOM(parent_sku=self.raw, component_sku=self.parent, quantity=1)
        with self.assertRaises(ValidationError):
            bom.save()

    def test_invalid_bom_with_same_parent_and_component(self):
        with self.assertRaises(ValidationError):
            BOM.objects.create(parent_sku=self.parent, component_sku=self.parent, quantity=1)

    def test_invalid_bom_with_zero_quantity(self):
        with self.assertRaises(ValidationError):
            BOM.objects.create(parent_sku=self.parent, component_sku=self.raw, quantity=0)

    def test_duplicate_component_for_same_parent(self):
        BOM.objects.create(parent_sku=self.parent, component_sku=self.raw, quantity=1)
        with self.assertRaises(ValidationError):
            BOM.objects.create(parent_sku=self.parent, component_sku=self.raw, quantity=2)

    def test_update_bom_when_locked(self):
        bom = BOM.objects.create(parent_sku=self.parent, component_sku=self.raw, quantity=1)
        self.parent.is_bom_locked = True
        self.parent.save()
        bom.quantity = 2
        with self.assertRaises(ValidationError):
            bom.save()

    def test_optimistic_locking_fail(self):
        bom = BOM.objects.create(parent_sku=self.parent, component_sku=self.raw, quantity=1)
        # Simulate concurrent update
        bom_in_db = BOM.objects.get(pk=bom.pk)
        bom_in_db.quantity += 1
        bom_in_db.save()
        self.assertEqual(bom.version, 0)  # Original version should not change
        self.assertEqual(bom_in_db.version, 1)  # Updated version should be 1
        bom.quantity = 2
        with self.assertRaises(ValidationError):
            bom.save()
