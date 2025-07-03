from django.test import TestCase
from catalog.models import ItemSKU
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class ItemRulesTest(TestCase):

    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        # Create a sample ItemSKU object for testing
        self.item = ItemSKU.objects.create(
            sku_code='SKU01',
            name='Test Item',
            unit='pcs',
            type='RAW',
            status='ACTIVE',
            created_by=self.user,
            updated_by=self.user,
        )

    # Raw Item on creation is_locked should be true
    def test_raw_item_creation_is_locked(self):
        raw_item = ItemSKU.objects.create(
            sku_code='SKU02',
            name='Raw Item',
            unit='kg',
            type='RAW',
            status='ACTIVE',
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertTrue(raw_item.is_bom_locked, "Raw item should be locked on creation.")

    # Product or Package Item on creation is_locked should be false
    def test_product_or_package_item_creation_is_not_locked(self):
        product_item = ItemSKU.objects.create(
            sku_code='SKU03',
            name='Product Item',
            unit='pcs',
            type='PRODUCT',
            status='ACTIVE',
            created_by=self.user,
            updated_by=self.user,
        )
        package_item = ItemSKU.objects.create(
            sku_code='SKU04',
            name='Package Item',
            unit='box',
            type='PACKAGE',
            status='ACTIVE',
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertFalse(product_item.is_bom_locked, "Product item should not be locked on creation.")
        self.assertFalse(package_item.is_bom_locked, "Package item should not be locked on creation.")

    # Item type cannot be changed once set
    def test_item_type_cannot_change(self):
        self.item.type = 'PRODUCT'
        with self.assertRaises(ValidationError) as context:
            self.item.save()
        self.assertIn("Item type cannot be changed once set.", str(context.exception))
    
    # SKU code must be unique and cannot be changed once set
    def test_sku_code_cannot_change(self):
        self.item.sku_code = 'SKU02'
        with self.assertRaises(ValidationError) as context:
            self.item.save()
        self.assertIn("SKU code must be unique and cannot be changed once set.", str(context.exception))
    
    


