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

    def test_item_type_cannot_change(self):
        # Attempt to change the type of an existing item
        self.item.type = 'PRODUCT'
        with self.assertRaises(ValidationError):
            self.item.save()

