from django.test import TestCase
from catalog.models.item import ItemSKU
from catalog.models.bom import BOM
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class BOMModelTest(TestCase):
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

    def test_bom_creation_1(self):
        bom = BOM.objects.create(
            parent_sku=self.product,
            component_sku=self.item1,
            quantity=10
        )
        self.assertEqual(str(bom), 'SKU04 needs 10 x SKU01')

    def test_bom_creation_2(self):
        bom = BOM.objects.create(
            parent_sku=self.product,
            component_sku=self.item2,
            quantity=5
        )
        self.assertEqual(str(bom), 'SKU04 needs 5 x SKU02')


        
