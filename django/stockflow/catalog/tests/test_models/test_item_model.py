from django.test import TestCase
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class ItemSKUModelTest(TestCase):
    def setUp(self):
        # Create users for testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword2'
        )
        
        # Create categories for testing
        self.active_category = Category.objects.create(
            name='Active Category',
            created_by=self.user,
            updated_by=self.user,
            is_active=True
        )
        
        self.inactive_category = Category.objects.create(
            name='Inactive Category',
            created_by=self.user,
            updated_by=self.user,
            is_active=False
        )
        
        # Create sample items for testing
        self.raw_item = ItemSKU.objects.create(
            sku_code='RAW-001',
            name='Raw Material',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.product_item = ItemSKU.objects.create(
            sku_code='PROD-001',
            name='Product Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.package_item = ItemSKU.objects.create(
            sku_code='PKG-001',
            name='Package Item',
            unit='pcs',
            type=ItemSKU.Type.PACKAGE,
            status=ItemSKU.Status.DRAFT,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )

    # Basic creation and validation tests
    
    def test_create_item_success(self):
        """Test creating an item successfully"""
        item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.sku_code, 'TEST-001')
        self.assertEqual(item.status, ItemSKU.Status.ACTIVE)  # Default for RAW
        self.assertEqual(item.version, 0)
    
    def test_item_string_representation(self):
        """Test the string representation of an item"""
        self.assertEqual(str(self.raw_item), 'RAW-001 - Raw Material')
    
    def test_whitespace_cleaning(self):
        """Test that whitespace is cleaned from fields"""
        item = ItemSKU(
            sku_code='  TEST-002  ',
            name='  Spaces Item  ',
            unit='  pcs  ',
            type=ItemSKU.Type.RAW,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        item.save()
        
        self.assertEqual(item.sku_code, 'TEST-002')
        self.assertEqual(item.name, 'Spaces Item')
        self.assertEqual(item.unit, 'pcs')
    
    # # Field validation tests
    
    def test_empty_sku_code_validation(self):
        """Test validation for empty SKU code"""
        item = ItemSKU(
            sku_code='',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            item.save()
        
        self.assertIn("SKU code is required", str(context.exception))
    
    def test_empty_name_validation(self):
        """Test validation for empty name"""
        item = ItemSKU(
            sku_code='TEST-003',
            name='',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            item.save()
        
        self.assertIn("Item name is required", str(context.exception))
    
    def test_empty_unit_validation(self):
        """Test validation for empty unit"""
        item = ItemSKU(
            sku_code='TEST-004',
            name='Test Item',
            unit='',
            type=ItemSKU.Type.RAW,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            item.save()
        
        self.assertIn("Unit is required", str(context.exception))
    
    def test_inactive_category_validation(self):
        """Test validation when assigning to inactive category"""
        item = ItemSKU(
            sku_code='TEST-005',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.inactive_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            item.save()
        
        self.assertIn("Cannot assign item to inactive category", str(context.exception))
    
    # # Business logic tests
    
    def test_raw_material_cannot_be_draft(self):
        """Test that raw materials cannot be in DRAFT status"""
        item = ItemSKU(
            sku_code='TEST-006',
            name='Raw Test',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.DRAFT,  # This should fail
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            item.save()
        
        self.assertIn("Raw materials cannot be in DRAFT status", str(context.exception))
    
    def test_initial_state_for_raw(self):
        """Test initial state for RAW materials is always ACTIVE"""
        item = ItemSKU(
            sku_code='TEST-007',
            name='Raw Item',
            unit='kg',
            type=ItemSKU.Type.RAW,
            # Not setting status - should default to ACTIVE
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        item.save()
        
        self.assertEqual(item.status, ItemSKU.Status.ACTIVE)
    
    def test_initial_state_for_product(self):
        """Test initial state for PRODUCT is DRAFT"""
        item = ItemSKU(
            sku_code='TEST-008',
            name='Product Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            # Not setting status - should be set to DRAFT
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        item.save()
        
        self.assertEqual(item.status, ItemSKU.Status.DRAFT)
    
    def test_cannot_change_sku_code(self):
        """Test that SKU code cannot be changed after creation"""
        self.raw_item.sku_code = 'CHANGED-001'
        
        with self.assertRaises(ValueError) as context:
            self.raw_item.save()
        
        self.assertIn("SKU code cannot be changed once set", str(context.exception))
    
    def test_cannot_change_type(self):
        """Test that item type cannot be changed after creation"""
        self.raw_item.type = ItemSKU.Type.PRODUCT
        
        with self.assertRaises(ValueError) as context:
            self.raw_item.save()
        
        self.assertIn("Item type cannot be changed once set", str(context.exception))
    
    def test_optimistic_locking(self):
        """Test optimistic locking prevents concurrent updates"""
        # Get the same item twice
        item1 = ItemSKU.objects.get(pk=self.raw_item.pk)
        item2 = ItemSKU.objects.get(pk=self.raw_item.pk)
        
        # Update the first one
        item1.name = "Updated Name"
        item1.save()
        
        # Try to update the second one with stale version
        item2.name = "Conflicting Update"
        with self.assertRaises(ValueError) as context:
            item2.save()
        
        self.assertIn("modified by another user", str(context.exception))
    
    # BOM-related business logic tests
    
    def test_can_have_bom_logic(self):
        """Test can_have_bom business logic"""
        self.assertFalse(self.raw_item.can_have_bom())
        self.assertTrue(self.product_item.can_have_bom())
        self.assertTrue(self.package_item.can_have_bom())
    
    def test_is_bom_locked_logic(self):
        """Test is_bom_locked business logic"""
        self.assertTrue(self.raw_item.is_bom_locked())  # RAW is always locked
        self.assertFalse(self.product_item.is_bom_locked())  # DRAFT is not locked
        
        # Lock the product and check again
        self.product_item.status = ItemSKU.Status.ACTIVE
        self.product_item.save()
        self.assertTrue(self.product_item.is_bom_locked())
    
    def test_allows_bom_changes_logic(self):
        """Test allows_bom_changes business logic"""
        self.assertFalse(self.raw_item.is_allows_bom_changes())  # RAW can't have BOM
        self.assertTrue(self.product_item.is_allows_bom_changes())  # PRODUCT in DRAFT can
        
        # Lock the product and check again
        self.product_item.status = ItemSKU.Status.ACTIVE
        self.product_item.save()
        self.assertFalse(self.product_item.is_allows_bom_changes())
    
    def test_lock_bom(self):
        """Test locking a BOM"""
        # Should change status from DRAFT to ACTIVE
        self.assertEqual(self.product_item.status, ItemSKU.Status.DRAFT)
        self.product_item.lock_bom()
        self.product_item.save()
        self.assertEqual(self.product_item.status, ItemSKU.Status.ACTIVE)
        
        # Cannot lock BOM for RAW materials
        with self.assertRaises(ValueError) as context:
            self.raw_item.lock_bom()
        
        self.assertIn("cannot have a BOM", str(context.exception))
    
    def test_unlock_bom(self):
        """Test unlocking a BOM"""
        # First make it ACTIVE
        self.product_item.status = ItemSKU.Status.ACTIVE
        self.product_item.save()
        
        # Then unlock it
        self.assertEqual(self.product_item.status, ItemSKU.Status.ACTIVE)
        self.product_item.unlock_bom()
        self.product_item.save()
        self.assertEqual(self.product_item.status, ItemSKU.Status.DRAFT)
        
        # Cannot unlock BOM for RAW materials
        with self.assertRaises(ValueError) as context:
            self.raw_item.unlock_bom()
        
        self.assertIn("cannot have a BOM", str(context.exception))
    
    # # Status helper methods tests
    
    def test_status_helper_methods(self):
        """Test status helper methods"""
        # Active item
        active_item = ItemSKU.objects.create(
            sku_code='ACTIVE-001',
            name='Active Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertTrue(active_item.is_active())
        self.assertFalse(active_item.is_draft())
        
        # Draft item
        self.assertTrue(self.product_item.is_draft())
        self.assertFalse(self.product_item.is_active())
        
        # Inactive item
        inactive_item = ItemSKU.objects.create(
            sku_code='INACTIVE-001',
            name='Inactive Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.INACTIVE,
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertFalse(inactive_item.is_active())
        # When creating a new item, the save() method calls _set_initial_state()
        # which sets PRODUCT and PACKAGE items to DRAFT status regardless of the initial status value
        # So even though we specified INACTIVE, the item's status is actually DRAFT after saving
        self.assertTrue(inactive_item.is_draft())
