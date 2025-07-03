from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU, ItemSKUType, ItemSKUStatus
from catalog.models.category import Category
from django.core.exceptions import ValidationError

class ItemSKUModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.category = Category.objects.create(
            name='Chemicals',
            created_by=self.user,
            updated_by=self.user
        )

    def create_item(self, **kwargs):
        return ItemSKU.objects.create(
            sku_code=kwargs.get('sku_code', 'ITEM001'),
            name=kwargs.get('name', 'Test Item'),
            unit=kwargs.get('unit', 'pcs'),
            type=kwargs.get('type', ItemSKUType.RAW),
            status=kwargs.get('status', ItemSKUStatus.ACTIVE),
            created_by=self.user,
            updated_by=self.user,
            category=self.category,
            description=kwargs.get('description', '')
        )

    def test_create_item_success(self):
        item = self.create_item()
        self.assertEqual(item.sku_code, 'ITEM001')
        self.assertEqual(item.version, 0)
        self.assertTrue(item.is_bom_locked) # Raw items should be locked by default
        
    def test_cannot_change_sku_code_after_creation(self):
        item = self.create_item()
        item.sku_code = 'ITEM002'
        with self.assertRaises(ValidationError) as context:
            item.save()
        self.assertIn("SKU code must be unique and cannot be changed once set", str(context.exception))

    def test_cannot_change_type_after_creation(self):
        item = self.create_item()
        item.type = ItemSKUType.PRODUCT
        with self.assertRaises(ValidationError) as context:
            item.save()
        self.assertIn("Item type cannot be changed", str(context.exception))

    def test_optimistic_locking_fail(self):
        item = self.create_item()
        item.version = 999  # Wrong version
        item.name = "Changed Name"
        with self.assertRaises(ValidationError) as context:
            item.save()
        self.assertIn("Optimistic Locking failed", str(context.exception))

    def test_success_update_with_correct_version(self):
        item = self.create_item()
        original_version = item.version

        item.name = "Updated"
        item.version = original_version  # Must match
        item.save()

        item.refresh_from_db()
        self.assertEqual(item.name, "Updated")
        self.assertEqual(item.version, original_version + 1)
        
    def test_bom_locking(self):
        item = self.create_item()
        item.is_bom_locked = True
        item.save()

        # Try to unlock the BOM
        item.is_bom_locked = False
        with self.assertRaises(ValidationError) as context:
            item.save()
        self.assertIn("Cannot unlock a BOM once it has been locked", str(context.exception))

    def test_create_item_with_category(self):
        item = self.create_item(category=self.category)
        self.assertEqual(item.category, self.category)
        self.assertEqual(item.category.name, 'Chemicals')
        
        