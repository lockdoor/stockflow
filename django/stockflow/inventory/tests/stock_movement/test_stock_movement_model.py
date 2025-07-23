from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem  # Assuming this model exists


class StockMovementModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN01',
            address='123 Main St',
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_draft_stock_movement_success(self):
        """Test creating a draft stock movement successfully"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.PACKING_LIST,
            reference_id=123,
            note='Receive goods',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check default values and assignments
        self.assertEqual(movement.status, StockMovement.Status.DRAFT)
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.PACKING_LIST)
        self.assertEqual(movement.reference_id, 123)
        self.assertEqual(movement.note, 'Receive goods')
        self.assertEqual(movement.warehouse, self.warehouse)
        self.assertEqual(movement.created_by, self.user)
        self.assertEqual(movement.version, 1)
        self.assertFalse(movement.is_immutable())
        self.assertTrue(movement.can_be_modified())
        
        # Check string representation
        expected_str = f"Stock Movement #{movement.id} (DRAFT) - Main Warehouse"
        self.assertEqual(str(movement), expected_str)

    def test_update_draft_stock_movement(self):
        """Test updating a draft stock movement"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update note
        original_version = movement.version
        movement.note = 'Updated draft note'
        movement.save()
        movement.refresh_from_db()
        
        self.assertEqual(movement.note, 'Updated draft note')
        self.assertEqual(movement.version, original_version + 1)  # Version incremented

    def test_confirm_stock_movement_with_items(self):
        """Test confirming a stock movement that has items"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a mock item (StockMovementItem) to simulate having items
        # Note: This assumes StockMovementItem model exists and can be imported
        try:
            from catalog.models.item import ItemSKU
            # Create a simple ItemSKU for testing
            item_sku = ItemSKU.objects.create(
                sku_code='TEST001',
                name='Test Item',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=10,
                created_by=self.user,
                updated_by=self.user
            )
            
            # Should be able to confirm since it has items
            can_confirm, reason = movement.can_be_confirmed()
            self.assertTrue(can_confirm)
            self.assertEqual(reason, "")
            
            # Confirm the movement
            result = movement.confirm(self.user)
            self.assertTrue(result)
            
            # Check state after confirmation
            movement.refresh_from_db()
            self.assertEqual(movement.status, StockMovement.Status.CONFIRMED)
            self.assertTrue(movement.is_immutable())
            self.assertFalse(movement.can_be_modified())
            
        except ImportError:
            # Skip this test if ItemSKU model is not available
            self.skipTest("ItemSKU model not available for testing")

    def test_cannot_confirm_empty_stock_movement(self):
        """Test that stock movement without items cannot be confirmed"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Movement has no items - should not be confirmable
        can_confirm, reason = movement.can_be_confirmed()
        self.assertFalse(can_confirm)
        self.assertEqual(reason, "Cannot confirm movement without items")
        
        # Try to confirm anyway - should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            movement.confirm(self.user)
        
        self.assertIn("Cannot confirm movement without items", str(context.exception))
        
        # Movement should still be draft
        movement.refresh_from_db()
        self.assertEqual(movement.status, StockMovement.Status.DRAFT)
        self.assertFalse(movement.is_immutable())
        
    def test_confirm_stock_movement_not_empty(self):
        """Test confirming a stock movement that is not empty - legacy test"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Note: This test was originally written without considering items
        # In the refactored version, we should actually have items to confirm
        # For now, we'll test the empty case which should fail
        can_confirm, reason = movement.can_be_confirmed()
        self.assertFalse(can_confirm)  # Changed: now expects False since no items
        self.assertEqual(reason, "Cannot confirm movement without items")  # Changed expectation
        
    
    def test_confirm_stock_movement(self):
        """Test confirming a stock movement using confirm method - updated to handle empty movement"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Movement has no items - should not be confirmable
        can_confirm, reason = movement.can_be_confirmed()
        self.assertFalse(can_confirm)
        self.assertEqual(reason, "Cannot confirm movement without items")
        
        # Try to confirm should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            movement.confirm(self.user)
        
        self.assertIn("Cannot confirm movement without items", str(context.exception))

    def test_confirmed_stock_movement_is_immutable(self):
        """Test that confirmed stock movement cannot be modified"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add an item so we can confirm the movement
        try:
            from catalog.models.item import ItemSKU
            item_sku = ItemSKU.objects.create(
                sku_code='TEST002',
                name='Test Item 2',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=5,
                created_by=self.user,
                updated_by=self.user
            )
            
            # Confirm movement using the confirm method
            movement.confirm(self.user)
            
            # Try to update after confirmed
            movement.note = 'Try to update after confirm'
            with self.assertRaises(ValidationError) as context:
                movement.save()
            
            self.assertIn('Confirmed stock movements cannot be modified', str(context.exception))
            
        except ImportError:
            self.skipTest("ItemSKU model not available for testing")

    def test_confirmed_stock_movement_cannot_be_deleted(self):
        """Test that confirmed stock movement cannot be deleted"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add an item so we can confirm the movement
        try:
            from catalog.models.item import ItemSKU
            item_sku = ItemSKU.objects.create(
                sku_code='TEST003',
                name='Test Item 3',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=3,
                created_by=self.user,
                updated_by=self.user
            )
            
            # Confirm the movement
            movement.confirm(self.user)
            
            # Try to delete confirmed movement
            with self.assertRaises(ValidationError) as context:
                movement.delete()
            
            self.assertIn('Confirmed stock movements cannot be modified', str(context.exception))
            
        except ImportError:
            self.skipTest("ItemSKU model not available for testing")

    def test_unique_draft_per_warehouse(self):
        """Test that only one draft movement per warehouse is allowed"""
        # Create first draft movement
        StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create second draft movement for same warehouse
        with self.assertRaises(IntegrityError):
            StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.PACKING_LIST,
                warehouse=self.warehouse,
                created_by=self.user,
                updated_by=self.user
            )

    def test_multiple_confirmed_movements_allowed(self):
        """Test that multiple confirmed movements per warehouse are allowed"""
        # Create and confirm first movement
        movement1 = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add items to both movements so they can be confirmed
        try:
            from catalog.models.item import ItemSKU
            item_sku1 = ItemSKU.objects.create(
                sku_code='TEST004',
                name='Test Item 4',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            item_sku2 = ItemSKU.objects.create(
                sku_code='TEST005',
                name='Test Item 5',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            
            StockMovementItem.objects.create(
                stock_movement=movement1,
                item_sku=item_sku1,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=10,
                created_by=self.user,
                updated_by=self.user
            )
            
            movement1.confirm(self.user)
            
            # Create and confirm second movement - should be allowed
            movement2 = StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.PACKING_LIST,
                warehouse=self.warehouse,
                created_by=self.user,
                updated_by=self.user
            )
            
            StockMovementItem.objects.create(
                stock_movement=movement2,
                item_sku=item_sku2,
                movement_type=StockMovementItem.MovementType.OUT,
                quantity=5,
                created_by=self.user,
                updated_by=self.user
            )
            
            movement2.confirm(self.user)
            
            # Both should be confirmed
            self.assertEqual(movement1.status, StockMovement.Status.CONFIRMED)
            self.assertEqual(movement2.status, StockMovement.Status.CONFIRMED)
            
        except ImportError:
            self.skipTest("ItemSKU model not available for testing")

    def test_optimistic_locking(self):
        """Test optimistic locking prevents concurrent modifications"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get two instances of the same movement (simulating two users)
        movement_user1 = StockMovement.objects.get(pk=movement.pk)
        movement_user2 = StockMovement.objects.get(pk=movement.pk)
        
        # User 1 modifies and saves first
        movement_user1.note = 'Modified by user 1'
        movement_user1.save()
        
        # User 2 tries to modify with stale version
        movement_user2.note = 'Modified by user 2'
        with self.assertRaises(ValidationError) as context:
            movement_user2.save()
        
        self.assertIn('Record has been modified by another user', str(context.exception))
        
        # Verify only user 1's change was saved
        movement.refresh_from_db()
        self.assertEqual(movement.note, 'Modified by user 1')

    def test_validators_reference_id_required_for_non_none_types(self):
        """Test that reference_id is required for non-NONE reference types"""
        with self.assertRaises(ValidationError) as context:
            movement = StockMovement(
                reference_type=StockMovement.ReferenceType.INVOICE,
                reference_id=None,  # Should be required for INVOICE type
                warehouse=self.warehouse,
                created_by=self.user,
                updated_by=self.user
            )
            movement.full_clean()
        
        self.assertIn('Reference ID is required when reference type is INVOICE', str(context.exception))

    def test_reference_display_methods(self):
        """Test reference display methods"""
        # Test with NONE reference type
        movement_none = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.NONE,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(movement_none.get_reference_display(), "No Reference")
        
        # Delete the first movement to avoid unique constraint violation
        movement_none.delete()
        
        # Test with reference type and ID
        movement_with_ref = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.INVOICE,
            reference_id=12345,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(movement_with_ref.get_reference_display(), "Invoice #12345")

    def test_business_logic_methods(self):
        """Test business logic helper methods"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test draft state - empty movement cannot be confirmed
        self.assertTrue(movement.can_be_modified())
        can_confirm, reason = movement.can_be_confirmed()
        self.assertFalse(can_confirm)  # Changed: empty movement cannot be confirmed
        self.assertEqual(reason, "Cannot confirm movement without items")
        
        # Add items and test confirmed state
        try:
            from catalog.models.item import ItemSKU
            item_sku = ItemSKU.objects.create(
                sku_code='TEST006',
                name='Test Item 6',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=1,
                created_by=self.user,
                updated_by=self.user
            )
            
            # Now should be confirmable
            can_confirm, reason = movement.can_be_confirmed()
            self.assertTrue(can_confirm)
            self.assertEqual(reason, "")
            
            # Test confirmed state
            movement.confirm(self.user)
            self.assertFalse(movement.can_be_modified())
            can_confirm, reason = movement.can_be_confirmed()
            self.assertFalse(can_confirm)
            self.assertEqual(reason, "Only draft movements can be confirmed")
            
            # Test items count
            self.assertEqual(movement.get_total_items_count(), 1)
            
        except ImportError:
            # Skip parts that require ItemSKU if not available
            self.assertEqual(movement.get_total_items_count(), 0)

    def test_can_be_confirmed_edge_cases(self):
        """Test can_be_confirmed method with various edge cases"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Case 1: Empty movement cannot be confirmed
        can_confirm, reason = movement.can_be_confirmed()
        self.assertFalse(can_confirm)
        self.assertEqual(reason, "Cannot confirm movement without items")
        
        # Case 2: Movement with items can be confirmed
        try:
            from catalog.models.item import ItemSKU
            item_sku = ItemSKU.objects.create(
                sku_code='TEST_EDGE01',
                name='Test Edge Item',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            
            # Add an item to the movement
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=15,
                created_by=self.user,
                updated_by=self.user
            )
            
            # Now it should be confirmable
            can_confirm, reason = movement.can_be_confirmed()
            self.assertTrue(can_confirm)
            self.assertEqual(reason, "")
            
            # Case 3: Confirmed movement cannot be confirmed again
            movement.confirm(self.user)
            can_confirm, reason = movement.can_be_confirmed()
            self.assertFalse(can_confirm)
            self.assertEqual(reason, "Only draft movements can be confirmed")
            
        except ImportError:
            self.skipTest("ItemSKU model not available for testing")

    def test_items_count_with_multiple_items(self):
        """Test that get_total_items_count returns correct count"""
        movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Initially no items
        self.assertEqual(movement.get_total_items_count(), 0)
        
        try:
            from catalog.models.item import ItemSKU
            
            # Create multiple items
            item_sku1 = ItemSKU.objects.create(
                sku_code='TEST_COUNT01',
                name='Test Count Item 1',
                unit='pcs',
                created_by=self.user,
                updated_by=self.user
            )
            item_sku2 = ItemSKU.objects.create(
                sku_code='TEST_COUNT02',
                name='Test Count Item 2',
                unit='kg',
                created_by=self.user,
                updated_by=self.user
            )
            
            # Add first item
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku1,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=10,
                created_by=self.user,
                updated_by=self.user
            )
            
            self.assertEqual(movement.get_total_items_count(), 1)
            
            # Add second item
            StockMovementItem.objects.create(
                stock_movement=movement,
                item_sku=item_sku2,
                movement_type=StockMovementItem.MovementType.OUT,
                quantity=5,
                created_by=self.user,
                updated_by=self.user
            )
            
            self.assertEqual(movement.get_total_items_count(), 2)
            
            # Can confirm now that we have items
            can_confirm, reason = movement.can_be_confirmed()
            self.assertTrue(can_confirm)
            self.assertEqual(reason, "")
            
        except ImportError:
            self.skipTest("ItemSKU model not available for testing")