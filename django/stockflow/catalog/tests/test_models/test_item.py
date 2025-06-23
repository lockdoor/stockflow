from django.test import TestCase
from catalog.models.item import ItemSKU
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class ItemSKUModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        ItemSKU.objects.create(
            sku_code='SKU01',
            name='Test Item',
            unit='pcs',
            created_by=self.user,
            updated_by=self.user,
        )
        
    def test_status_default(self):
        item = ItemSKU.objects.create(
            sku_code='SKU02',
            name='Test Item',
            unit='pcs',
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.status, 'ACTIVE')
        self.assertEqual(item.type, 'RAW')
        self.assertIsNone(item.category)

    def test_unique_sku_code(self):
        with self.assertRaises(Exception):
            ItemSKU.objects.create(
                sku_code='SKU01',
                name='Duplicate Item',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user,
            )

    def test_str_representation(self):
        item = ItemSKU.objects.get(sku_code='SKU01')
        self.assertEqual(str(item), 'SKU01 - Test Item')

    def test_invalid_type(self):
        item = ItemSKU(
            sku_code='SKU03',
            name='Invalid Type Item',
            unit='pcs',
            type='INVALID_TYPE',
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_invalid_status(self):
        item = ItemSKU(
            sku_code='SKU03',
            name='Invalid Type Item',
            unit='pcs',
            status='INVALID_STATUS',
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()
