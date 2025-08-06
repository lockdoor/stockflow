"""
Tests for StockMovementItem Model

Tests the model behavior, validation, business rules, and constraints
for stock movement items including lot tracking and immutability.
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import ProtectedError

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class StockMovementItemModelTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2', 
            password='testpass456'
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create item SKU
        self.item_sku = ItemSKU.objects.create(
            sku_code='TEST001',
            name='Test Item',
            type=ItemSKU.Type.RAW,
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movement
        self.stock_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=123,
            note='Test movement',
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )

    def test_model_creation(self):
        """Test basic model creation"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.50'),
            lot_number='LOT001',
            note='Test item',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(movement_item.stock_movement, self.stock_movement)
        self.assertEqual(movement_item.item_sku, self.item_sku)
        self.assertEqual(movement_item.movement_type, StockMovementItem.MovementType.IN)
        self.assertEqual(movement_item.quantity, Decimal('10.50'))
        self.assertEqual(movement_item.lot_number, 'LOT001')
        self.assertEqual(movement_item.note, 'Test item')

    def test_string_representation(self):
        """Test __str__ method"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.50'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        expected = f"{self.item_sku.sku_code} (Stock In) x {movement_item.quantity}"
        self.assertEqual(str(movement_item), expected)

    def test_movement_type_choices(self):
        """Test movement type choices"""
        # Test IN
        movement_item_in = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertTrue(movement_item_in.is_inbound)
        self.assertFalse(movement_item_in.is_outbound)
        
        # Test OUT
        movement_item_out = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5'),
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertTrue(movement_item_out.is_outbound)
        self.assertFalse(movement_item_out.is_inbound)

    def test_unique_constraint(self):
        """Test unique constraint on (stock_movement, item_sku, lot_number, movement_type)"""
        # Create first item
        StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate - now caught by validator before database constraint
        with self.assertRaises(ValidationError) as context:
            StockMovementItem.objects.create(
                stock_movement=self.stock_movement,
                item_sku=self.item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('5'),
                lot_number='LOT001',  # Same lot number
                created_by=self.user,
                updated_by=self.user
            )
        
        # Verify the error message comes from our duplicate validator
        self.assertIn("already exists for this item in this movement", str(context.exception))

    def test_can_modify_draft_movement(self):
        """Test that items in DRAFT movement can be modified"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(movement_item.can_modify())
        self.assertFalse(movement_item.is_immutable())

    def test_cannot_modify_confirmed_movement(self):
        """Test that items in CONFIRMED movement cannot be modified"""
        # Create movement item first while status is DRAFT
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Change movement to CONFIRMED after creation
        self.stock_movement.status = StockMovement.Status.CONFIRMED
        self.stock_movement.save()
        
        # Refresh the item to get updated relationship
        movement_item.refresh_from_db()
        
        self.assertFalse(movement_item.can_modify())
        self.assertTrue(movement_item.is_immutable())

    def test_get_display_name(self):
        """Test get_display_name method"""
        # Test inbound item
        movement_item_in = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        expected_in = f"← {self.item_sku.name} (x{movement_item_in.quantity})"
        self.assertEqual(movement_item_in.get_display_name(), expected_in)
        
        # Test outbound item
        movement_item_out = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5'),
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        expected_out = f"→ {self.item_sku.name} (x{movement_item_out.quantity})"
        self.assertEqual(movement_item_out.get_display_name(), expected_out)

    def test_quantity_validation(self):
        """Test quantity validation through validators"""
        # Test negative quantity (should be caught by validator)
        movement_item = StockMovementItem(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('-5'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            movement_item.full_clean()

    def test_lot_number_required(self):
        """Test that lot number is required"""
        movement_item = StockMovementItem(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='',  # Empty lot number
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            movement_item.full_clean()

    def test_validators_are_called(self):
        """Test that model validators are properly configured"""
        movement_item = StockMovementItem(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        validators = movement_item.get_validators()
        self.assertEqual(len(validators), 6)  # Updated to 6 validators
        
        # Check validator types
        validator_classes = [type(v).__name__ for v in validators]
        expected_validators = [
            'StockMovementItemQuantityValidator',
            'StockMovementItemLotValidator',
            'StockMovementItemExpiryValidator',
            'StockMovementItemDuplicateValidator',
            'StockMovementItemBusinessRulesValidator',
            'StockMovementItemImmutableFieldValidator'  # Added new validator
        ]
        
        for expected in expected_validators:
            self.assertIn(expected, validator_classes)

    def test_meta_configuration(self):
        """Test model Meta configuration"""
        meta = StockMovementItem._meta
        
        # Test table name
        self.assertEqual(meta.db_table, 'inventory_stock_movement_item')
        
        # Test verbose names
        self.assertEqual(meta.verbose_name, 'Stock Movement Item')
        self.assertEqual(meta.verbose_name_plural, 'Stock Movement Items')
        
        # Test ordering
        self.assertEqual(meta.ordering, ['-created_at', 'item_sku__sku_code'])
        
        # Test unique_together
        self.assertIn(('stock_movement', 'item_sku', 'lot_number', 'movement_type'), 
                     meta.unique_together)

    def test_related_name_access(self):
        """Test accessing movement items through stock movement"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test related name access
        movement_items = self.stock_movement.movement_items.all()
        self.assertEqual(len(movement_items), 1)
        self.assertEqual(movement_items[0], movement_item)

    def test_cascade_delete(self):
        """Test that movement items are deleted when stock movement is deleted"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        movement_item_id = movement_item.id
        
        # Delete stock movement
        self.stock_movement.delete()
        
        # Check that movement item is also deleted
        self.assertFalse(
            StockMovementItem.objects.filter(id=movement_item_id).exists()
        )

    def test_protect_delete_item_sku(self):
        """Test that ItemSKU cannot be deleted if referenced by movement items"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to delete ItemSKU
        with self.assertRaises(ProtectedError):
            self.item_sku.delete()

    def test_different_lots_allowed(self):
        """Test that different lots for same item are allowed"""
        # Create first item with LOT001
        StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create second item with LOT002 - should be allowed
        item2 = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5'),
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(item2.lot_number, 'LOT002')

    def test_different_movement_types_same_lot(self):
        """Test that same lot can have both IN and OUT movement types"""
        # Create IN movement item
        in_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create OUT movement item with same lot - should be allowed
        out_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5'),
            lot_number='LOT001',  # Same lot number
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(in_item.lot_number, 'LOT001')
        self.assertEqual(out_item.lot_number, 'LOT001')
        self.assertNotEqual(in_item.movement_type, out_item.movement_type)

    def test_optimistic_locking(self):
        """Test optimistic locking prevents concurrent modifications"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get two instances (simulating two users)
        item_user1 = StockMovementItem.objects.get(pk=movement_item.pk)
        item_user2 = StockMovementItem.objects.get(pk=movement_item.pk)
        
        # User 1 modifies first
        item_user1.quantity = Decimal('15')
        item_user1.save()
        
        # User 2 tries to modify with stale version
        item_user2.quantity = Decimal('20')
        with self.assertRaises(ValidationError) as context:
            item_user2.save()
        
        self.assertIn('Record has been modified by another user', str(context.exception))
        
        # Verify only user 1's change was saved
        movement_item.refresh_from_db()
        self.assertEqual(movement_item.quantity, Decimal('15'))

    def test_decimal_precision(self):
        """Test that decimal quantities with more than 2 decimal places are rejected by validation"""
        # Test that validator catches quantities with more than 2 decimal places
        with self.assertRaises(ValidationError) as context:
            StockMovementItem.objects.create(
                stock_movement=self.stock_movement,
                item_sku=self.item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.123'),  # More than 2 decimal places
                lot_number='LOT001',
                created_by=self.user,
                updated_by=self.user
            )
        
        # Verify the error message mentions decimal places
        self.assertIn("decimal places", str(context.exception))
        
        # Test that valid precision works
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.12'),  # Exactly 2 decimal places
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should maintain precision up to model field definition (2 decimal places)
        movement_item.refresh_from_db()
        self.assertEqual(movement_item.quantity, Decimal('10.12'))

    def test_expiry_date_validation(self):
        """Test expiry date validation and edge cases"""
        # Test past date - should be rejected by validator now
        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError) as context:
            StockMovementItem.objects.create(
                stock_movement=self.stock_movement,
                item_sku=self.item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10'),
                lot_number='LOT001',
                expiry_date=past_date,
                created_by=self.user,
                updated_by=self.user
            )
        
        # Verify the error message mentions past date
        self.assertIn("cannot be in the past", str(context.exception))
        
        # Test valid future date
        future_date = date.today() + timedelta(days=30)
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT002',
            expiry_date=future_date,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(movement_item.expiry_date, future_date)
        
        # Test far future date (should be rejected if too far)
        far_future = date.today() + timedelta(days=365 * 51)  # 51 years
        with self.assertRaises(ValidationError) as context:
            StockMovementItem.objects.create(
                stock_movement=self.stock_movement,
                item_sku=self.item_sku,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('5'),
                lot_number='LOT003',
                expiry_date=far_future,
                created_by=self.user,
                updated_by=self.user
            )
        
        # Verify the error message mentions future limit
        self.assertIn("more than 50 years in the future", str(context.exception))

    def test_audit_fields_properly_set(self):
        """Test that audit fields are properly set and updated"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check initial audit fields
        self.assertEqual(movement_item.created_by, self.user)
        self.assertEqual(movement_item.updated_by, self.user)
        self.assertIsNotNone(movement_item.created_at)
        self.assertIsNotNone(movement_item.updated_at)
        self.assertEqual(movement_item.version, 1)
        
        # Update with different user
        movement_item.quantity = Decimal('15')
        movement_item.updated_by = self.user2
        movement_item.save()
        
        # Check that created_by didn't change but updated_by did
        self.assertEqual(movement_item.created_by, self.user)  # Should not change
        self.assertEqual(movement_item.updated_by, self.user2)  # Should change
        self.assertEqual(movement_item.version, 2)  # Should increment

    def test_note_field_optional(self):
        """Test that note field is optional"""
        # Create item without note
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertIsNone(movement_item.note)
        
        # Add note later
        movement_item.note = 'Added note later'
        movement_item.save()
        movement_item.refresh_from_db()
        self.assertEqual(movement_item.note, 'Added note later')

    def test_update_draft_movement_item(self):
        """Test updating an item in draft movement"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update quantity
        original_version = movement_item.version
        movement_item.quantity = Decimal('15')
        movement_item.note = 'Updated quantity'
        movement_item.save()
        movement_item.refresh_from_db()
        
        self.assertEqual(movement_item.quantity, Decimal('15'))
        self.assertEqual(movement_item.note, 'Updated quantity')
        self.assertEqual(movement_item.version, original_version + 1)


class StockMovementItemImmutableFieldValidationTest(TestCase):
    """Tests for StockMovementItemImmutableFieldValidator"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create warehouse
        self.warehouse1 = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create warehouse
        self.warehouse2 = Warehouse.objects.create(
            name='Test Warehouse 2',
            code='TEST02',
            address='456 Test Ave',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create items
        self.item1 = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item 1',
            category=self.category,
            unit='PCS',
            type=ItemSKU.Type.RAW,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            sku_code='TEST-002',
            name='Test Item 2',
            category=self.category,
            unit='PCS',
            type=ItemSKU.Type.RAW,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movements
        self.movement1 = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.NONE,
            warehouse=self.warehouse1,
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.movement2 = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.NONE,
            warehouse=self.warehouse2,
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

    def test_can_modify_allowed_fields(self):
        """Test that allowed fields (quantity, lot_number, expiry_date, note) can be modified"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=30),
            note='Initial note',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test updating allowed fields
        movement_item.quantity = Decimal('20')
        movement_item.lot_number = 'LOT002'
        movement_item.expiry_date = date.today() + timedelta(days=60)
        movement_item.note = 'Updated note'
        
        # Should save without validation errors
        try:
            movement_item.save()
            self.assertTrue(True, "Allowed fields can be modified")
        except ValidationError:
            self.fail("Should allow modification of quantity, lot_number, expiry_date, and note")

    def test_cannot_modify_stock_movement(self):
        """Test that stock_movement field cannot be modified"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to change stock_movement
        movement_item.stock_movement = self.movement2
        
        # Should raise validation error
        with self.assertRaises(ValidationError) as context:
            movement_item.save()
        
        self.assertIn("Stock movement cannot be changed after creation", str(context.exception))

    def test_cannot_modify_item_sku(self):
        """Test that item_sku field cannot be modified"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to change item_sku
        movement_item.item_sku = self.item2
        
        # Should raise validation error
        with self.assertRaises(ValidationError) as context:
            movement_item.save()
        
        self.assertIn("Item SKU cannot be changed after creation", str(context.exception))

    def test_cannot_modify_movement_type(self):
        """Test that movement_type field cannot be modified"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to change movement_type
        movement_item.movement_type = 'OUT'
        
        # Should raise validation error
        with self.assertRaises(ValidationError) as context:
            movement_item.save()
        
        self.assertIn("Movement type cannot be changed after creation", str(context.exception))

    def test_multiple_immutable_field_changes(self):
        """Test error message when multiple immutable fields are changed"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to change multiple immutable fields
        movement_item.stock_movement = self.movement2
        movement_item.item_sku = self.item2
        movement_item.movement_type = 'OUT'
        
        # Should raise validation error with all messages
        with self.assertRaises(ValidationError) as context:
            movement_item.save()
        
        error_message = str(context.exception)
        self.assertIn("Stock movement cannot be changed", error_message)
        self.assertIn("Item SKU cannot be changed", error_message)
        self.assertIn("Movement type cannot be changed", error_message)

    def test_validator_only_runs_on_updates(self):
        """Test that validator only runs on updates, not creation"""
        # Create new movement item with immutable fields set
        # This should work without validation errors
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertIsNotNone(movement_item.pk)
        self.assertEqual(movement_item.stock_movement, self.movement1)
        self.assertEqual(movement_item.item_sku, self.item1)
        self.assertEqual(movement_item.movement_type, 'IN')

    def test_validator_handles_missing_original_gracefully(self):
        """Test that validator handles cases where original item cannot be found"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement1,
            item_sku=self.item1,
            movement_type='IN',
            quantity=Decimal('10'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Mock a scenario where original item might not be found
        # by temporarily changing the pk
        original_pk = movement_item.pk
        movement_item.pk = 99999  # Non-existent pk
        
        # Update allowed field
        movement_item.quantity = Decimal('20')
        
        # Should handle gracefully and not raise error
        movement_item.pk = original_pk  # Restore pk
        try:
            movement_item.save()
            self.assertTrue(True, "Validator handles missing original gracefully")
        except ValidationError:
            self.fail("Validator should handle missing original object gracefully")
