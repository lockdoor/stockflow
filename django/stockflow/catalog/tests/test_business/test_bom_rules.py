from django.test import TestCase
from catalog.models.item import ItemSKU
from catalog.models.bom import BOM
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class BOMBusinessRuleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.item1 = ItemSKU.objects.create(
            sku_code='SKU01',
            name='Test Item 1',
            unit='pcs',
            created_by=self.user,
            updated_by=self.user,
        )
        self.item2 = ItemSKU.objects.create(
            sku_code='SKU02',
            name='Test Item 2',
            unit='pcs',
            created_by=self.user,
            updated_by=self.user,
        )
        self.item3 = ItemSKU.objects.create(
            sku_code='SKU03',
            name='Test Item 3',
            unit='pcs',
            created_by=self.user,
            updated_by=self.user,
        )
        self.product = ItemSKU.objects.create(
            sku_code='SKU04',
            name='Test Product',
            unit='pcs',
            type='PRODUCT',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_bom_cannot_create_with_parent_is_raw_material(self):
        with self.assertRaises(ValidationError):
            BOM.objects.create(
                parent_sku=self.item1,  # item1 is a raw material
                component_sku=self.item2,
                quantity=3
            )

    def test_bom_quantity_validation(self):
        with self.assertRaises(ValidationError):
            BOM.objects.create(
                parent_sku=self.product,
                component_sku=self.item2,
                quantity=-5
            )

    def test_bom_parent_component_not_equal(self):
        with self.assertRaises(ValidationError):
            # Attempt to create a BOM where parent and component are the same
            BOM.objects.create(
                parent_sku=self.product,
                component_sku=self.product,
                quantity=2
            )

    def test_bom_cannot_update_when_is_locked(self):
        bom = BOM.objects.create(
            parent_sku=self.product,
            component_sku=self.item1,
            quantity=10
        )
        self.product.is_bom_locked = True
        self.product.save()
        with self.assertRaises(ValidationError):
            bom.quantity = 20
            bom.save()  # This should raise a ValidationError since BOM cannot be updated once created