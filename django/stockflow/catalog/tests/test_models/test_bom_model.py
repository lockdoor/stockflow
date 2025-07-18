from django.test import TestCase
from catalog.models.item import ItemSKU
from catalog.models.bom import BOM
from catalog.models.category import Category
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal

class BOMModelTest(TestCase):
    def setUp(self):
        """Set up test data for BOM model tests"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass2')
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for BOM tests',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create different types of items
        self.raw_material = ItemSKU.objects.create(
            sku_code='RAW001',
            name='Raw Material 1',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.raw_material2 = ItemSKU.objects.create(
            sku_code='RAW002',
            name='Raw Material 2',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.product_draft = ItemSKU.objects.create(
            sku_code='PROD001',
            name='Product 1 (Draft)',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.product_active = ItemSKU.objects.create(
            sku_code='PROD002',
            name='Product 2 (Active)',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.package_draft = ItemSKU.objects.create(
            sku_code='PKG001',
            name='Package 1 (Draft)',
            unit='box',
            type=ItemSKU.Type.PACKAGE,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.package_active = ItemSKU.objects.create(
            sku_code='PKG002',
            name='Package 2 (Active)',
            unit='box',
            type=ItemSKU.Type.PACKAGE,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )

    # ==================== VALID BOM CREATION TESTS ====================
    
    def test_valid_bom_creation_with_draft_parent(self):
        """Test creating valid BOM with DRAFT parent item"""
        bom = BOM(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.5'),
            created_by=self.user,
            updated_by=self.user
        )
        bom.save()
        self.assertEqual(BOM.objects.count(), 1)
        self.assertEqual(bom.parent_sku, self.product_draft)
        self.assertEqual(bom.component_sku, self.raw_material)
        self.assertEqual(bom.quantity, Decimal('1.5'))
        
    def test_valid_bom_creation_with_package_parent(self):
        """Test creating valid BOM with PACKAGE parent item"""
        bom = BOM.objects.create(
            parent_sku=self.package_draft,
            component_sku=self.raw_material,
            quantity=Decimal('2.0'),
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(BOM.objects.count(), 1)
        self.assertTrue(bom.parent_sku.can_have_bom())
        
    def test_valid_bom_creation_with_product_as_component(self):
        """Test creating BOM with another product as component"""
        bom = BOM.objects.create(
            parent_sku=self.package_draft,
            component_sku=self.product_active,
            quantity=Decimal('3.0'),
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(BOM.objects.count(), 1)
        self.assertTrue(bom.component_sku.can_be_component())

    # ==================== PARENT SKU VALIDATION TESTS ====================
    
    def test_invalid_bom_with_raw_parent(self):
        """Test that RAW materials cannot be parent in BOM"""
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.raw_material,
                component_sku=self.product_active,
                quantity=Decimal('1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("cannot have a BOM", str(context.exception))
        
    def test_invalid_bom_with_missing_parent(self):
        """Test BOM creation with missing parent SKU"""
        bom = BOM(
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("Parent SKU is required", str(context.exception))

    # ==================== COMPONENT SKU VALIDATION TESTS ====================
    
    def test_invalid_bom_with_missing_component(self):
        """Test BOM creation with missing component SKU"""
        bom = BOM(
            parent_sku=self.product_draft,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("Component SKU is required", str(context.exception))

    # ==================== QUANTITY VALIDATION TESTS ====================
    
    def test_invalid_bom_with_zero_quantity(self):
        """Test BOM creation with zero quantity"""
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.product_draft,
                component_sku=self.raw_material,
                quantity=Decimal('0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Quantity must be greater than zero", str(context.exception))
        
    def test_invalid_bom_with_negative_quantity(self):
        """Test BOM creation with negative quantity"""
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.product_draft,
                component_sku=self.raw_material,
                quantity=Decimal('-1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Quantity must be greater than zero", str(context.exception))
        
    def test_invalid_bom_with_missing_quantity(self):
        """Test BOM creation with missing quantity"""
        bom = BOM(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            created_by=self.user,
            updated_by=self.user
        )
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("Quantity is required", str(context.exception))

    # ==================== SELF REFERENCE VALIDATION TESTS ====================
    
    def test_invalid_bom_with_same_parent_and_component(self):
        """Test that parent and component cannot be the same"""
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.product_draft,
                component_sku=self.product_draft,
                quantity=Decimal('1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Parent SKU and component SKU cannot be the same", str(context.exception))

    # ==================== RECURSIVE RELATIONSHIP VALIDATION TESTS ====================
    
    def test_recursive_bom_two_level(self):
        """Test preventing direct recursive relationship (A -> B -> A)"""
        # Create A -> B
        BOM.objects.create(
            parent_sku=self.product_draft,  # A
            component_sku=self.package_draft,  # B
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create B -> A (should fail)
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.package_draft,  # B
                component_sku=self.product_draft,  # A
                quantity=Decimal('1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Recursive relationship detected", str(context.exception))
        
    def test_recursive_bom_three_level(self):
        """Test preventing three-level recursive relationship (A -> B -> C -> A)"""
        # Create third product for testing
        product3 = ItemSKU.objects.create(
            sku_code='PROD003',
            name='Product 3 (Draft)',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create A -> B
        BOM.objects.create(
            parent_sku=self.product_draft,  # A
            component_sku=self.package_draft,  # B
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create B -> C
        BOM.objects.create(
            parent_sku=self.package_draft,  # B
            component_sku=product3,  # C
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create C -> A (should fail)
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=product3,  # C
                component_sku=self.product_draft,  # A
                quantity=Decimal('1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Recursive relationship detected", str(context.exception))
        
    def test_valid_bom_no_recursion(self):
        """Test valid BOM creation that doesn't create recursion"""
        # Create A -> B
        BOM.objects.create(
            parent_sku=self.product_draft,  # A
            component_sku=self.package_draft,  # B
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create A -> C (should work)
        BOM.objects.create(
            parent_sku=self.product_draft,  # A
            component_sku=self.raw_material,  # C
            quantity=Decimal('2.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create B -> D (should work)
        BOM.objects.create(
            parent_sku=self.package_draft,  # B
            component_sku=self.raw_material2,  # D
            quantity=Decimal('3.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(BOM.objects.count(), 3)

    # ==================== DUPLICATE COMPONENT VALIDATION TESTS ====================
    
    def test_duplicate_component_for_same_parent(self):
        """Test preventing duplicate components in same parent BOM"""
        BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.product_draft,
                component_sku=self.raw_material,
                quantity=Decimal('2.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("This component already exists in the BOM", str(context.exception))
        
    def test_same_component_different_parents_allowed(self):
        """Test that same component can be used in different parent BOMs"""
        BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Same component in different parent should work
        BOM.objects.create(
            parent_sku=self.package_draft,
            component_sku=self.raw_material,
            quantity=Decimal('2.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(BOM.objects.count(), 2)

    # ==================== BOM LOCK VALIDATION TESTS ====================
    
    def test_bom_creation_with_locked_parent(self):
        """Test BOM creation when parent is locked (ACTIVE status)"""
        # Change product_active to ACTIVE after creation (since it starts as DRAFT)
        self.product_active.status = ItemSKU.Status.ACTIVE
        self.product_active.save()
        
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.product_active,  # ACTIVE status = locked
                component_sku=self.raw_material,
                quantity=Decimal('1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Cannot modify BOM when parent item is locked", str(context.exception))
        
    def test_bom_update_with_locked_parent(self):
        """Test BOM update when parent becomes locked"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,  # DRAFT status = unlocked
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Lock the parent
        self.product_draft.status = ItemSKU.Status.ACTIVE
        self.product_draft.save()
        
        # Try to update BOM (should fail)
        bom.quantity = Decimal('2.0')
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("Cannot modify BOM when parent item is locked", str(context.exception))

    def test_bom_creation_with_inactive_parent(self):
        """Test BOM creation when parent is INACTIVE status"""
        # Change product to INACTIVE after creation (since it starts as DRAFT)
        self.product_active.status = ItemSKU.Status.INACTIVE
        self.product_active.save()
        
        with self.assertRaises(ValueError) as context:
            BOM.objects.create(
                parent_sku=self.product_active,  # INACTIVE status = locked
                component_sku=self.raw_material,
                quantity=Decimal('1.0'),
                created_by=self.user,
                updated_by=self.user
            )
        self.assertIn("Cannot modify BOM when parent item is locked", str(context.exception))

    # ==================== UPDATE VALIDATION TESTS ====================
    
    def test_update_parent_sku_not_allowed(self):
        """Test that parent SKU cannot be changed once set"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        bom.parent_sku = self.package_draft
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("Parent SKU cannot be changed once set", str(context.exception))
        
    def test_update_component_sku_not_allowed(self):
        """Test that component SKU cannot be changed once set"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        bom.component_sku = self.raw_material2
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("Component SKU cannot be changed once set", str(context.exception))
        
    def test_valid_quantity_update(self):
        """Test valid quantity update"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        original_version = bom.version
        bom.quantity = Decimal('2.5')
        bom.updated_by = self.user2
        bom.save()
        
        bom.refresh_from_db()
        self.assertEqual(bom.quantity, Decimal('2.5'))
        self.assertEqual(bom.version, original_version + 1)
        self.assertEqual(bom.updated_by, self.user2)

    # ==================== OPTIMISTIC LOCKING TESTS ====================
    
    def test_optimistic_locking_success(self):
        """Test successful optimistic locking"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(bom.version, 0)
        bom.quantity = Decimal('2.0')
        bom.save()
        self.assertEqual(bom.version, 1)
        
    def test_optimistic_locking_fail(self):
        """Test optimistic locking failure with concurrent updates"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Simulate concurrent update
        bom_in_db = BOM.objects.get(pk=bom.pk)
        bom_in_db.quantity = Decimal('1.5')
        bom_in_db.updated_by = self.user2
        bom_in_db.save()
        
        # Original object version should not change
        self.assertEqual(bom.version, 0)
        # Updated object version should increment
        self.assertEqual(bom_in_db.version, 1)
        
        # Try to save original object (should fail)
        bom.quantity = Decimal('2.0')
        with self.assertRaises(ValueError) as context:
            bom.save()
        self.assertIn("has been modified by another user", str(context.exception))

    # ==================== BUSINESS LOGIC METHOD TESTS ====================
    
    def test_can_modify_with_draft_parent(self):
        """Test can_modify returns True for draft parent"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        self.assertTrue(bom.can_modify())
        
    def test_can_modify_with_locked_parent(self):
        """Test can_modify returns False for locked parent"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Lock the parent
        self.product_draft.status = ItemSKU.Status.ACTIVE
        self.product_draft.save()
        
        bom.refresh_from_db()
        self.assertFalse(bom.can_modify())
        
    def test_can_delete_with_draft_parent(self):
        """Test can_delete returns True for draft parent"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        self.assertTrue(bom.can_delete())
        
    def test_can_delete_with_locked_parent(self):
        """Test can_delete returns False for locked parent"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Lock the parent
        self.product_draft.status = ItemSKU.Status.ACTIVE
        self.product_draft.save()
        
        bom.refresh_from_db()
        self.assertFalse(bom.can_delete())

    # ==================== DISPLAY METHOD TESTS ====================
    
    def test_str_representation(self):
        """Test string representation of BOM"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('2.5'),
            created_by=self.user,
            updated_by=self.user
        )
        expected = f"{self.product_draft.sku_code} needs 2.5 x {self.raw_material.sku_code}"
        self.assertEqual(str(bom), expected)
        
    def test_get_component_display(self):
        """Test get_component_display method"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.5'),
            created_by=self.user,
            updated_by=self.user
        )
        expected = f"1.5 x {self.raw_material.sku_code} ({self.raw_material.name})"
        self.assertEqual(bom.get_component_display(), expected)
        
    def test_get_total_cost_returns_none(self):
        """Test get_total_cost returns None (placeholder implementation)"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        self.assertIsNone(bom.get_total_cost())

    # ==================== META AND DATABASE CONSTRAINT TESTS ====================
    
    def test_unique_together_constraint(self):
        """Test database unique constraint for parent/component combination"""
        BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Creating duplicate should fail at validation level, not database level
        with self.assertRaises(ValueError):
            BOM.objects.create(
                parent_sku=self.product_draft,
                component_sku=self.raw_material,
                quantity=Decimal('2.0'),
                created_by=self.user,
                updated_by=self.user
            )
            
    def test_model_ordering(self):
        """Test model ordering by parent and component SKU codes"""
        # Create multiple BOMs
        bom1 = BOM.objects.create(
            parent_sku=self.product_draft,  # PROD001
            component_sku=self.raw_material2,  # RAW002
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        bom2 = BOM.objects.create(
            parent_sku=self.product_draft,  # PROD001
            component_sku=self.raw_material,  # RAW001
            quantity=Decimal('2.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        bom3 = BOM.objects.create(
            parent_sku=self.package_draft,  # PKG001
            component_sku=self.raw_material,  # RAW001
            quantity=Decimal('3.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check ordering: PKG001, then PROD001 with RAW001 before RAW002
        boms = list(BOM.objects.all())
        self.assertEqual(len(boms), 3)
        self.assertEqual(boms[0], bom3)  # PKG001 + RAW001
        self.assertEqual(boms[1], bom2)  # PROD001 + RAW001
        self.assertEqual(boms[2], bom1)  # PROD001 + RAW002

    # ==================== AUDIT FIELD TESTS ====================
    
    def test_audit_fields_on_creation(self):
        """Test audit fields are properly set on creation"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(bom.created_by, self.user)
        self.assertEqual(bom.updated_by, self.user)
        self.assertIsNotNone(bom.created_at)
        self.assertIsNotNone(bom.updated_at)
        
    def test_audit_fields_on_update(self):
        """Test audit fields are properly updated on modification"""
        bom = BOM.objects.create(
            parent_sku=self.product_draft,
            component_sku=self.raw_material,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        original_created_at = bom.created_at
        original_created_by = bom.created_by
        
        # Update the BOM
        bom.quantity = Decimal('2.0')
        bom.updated_by = self.user2
        bom.save()
        
        bom.refresh_from_db()
        
        # created_* fields should not change
        self.assertEqual(bom.created_by, original_created_by)
        self.assertEqual(bom.created_at, original_created_at)
        
        # updated_* fields should change
        self.assertEqual(bom.updated_by, self.user2)
        self.assertGreater(bom.updated_at, original_created_at)
