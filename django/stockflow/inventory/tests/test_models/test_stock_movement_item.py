"""
Tests for StockMovementItem model

This module contains comprehensive tests for the refactored StockMovementItem model,
covering business logic, validation, and database constraints.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU, Category


class StockMovementItemModelTest(TestCase):
    """Test cases for StockMovementItem model"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test warehouse
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            address='Test Address',
            note='Test warehouse note',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item
        self.item = ItemSKU.objects.create(
            sku_code='TEST001',
            name='Test Item',
            unit='pcs',
            category=self.category,
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test stock movement
        self.stock_movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            warehouse=self.warehouse,
            note='Test movement',
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_valid_movement_item(self):
        """Test creating a valid movement item"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=30),
            note='Test note',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertIsNotNone(movement_item.id)
        self.assertEqual(movement_item.quantity, Decimal('10.00'))
        self.assertEqual(movement_item.lot_number, 'LOT001')
        self.assertTrue(movement_item.is_inbound)
        self.assertFalse(movement_item.is_outbound)

    def test_string_representation(self):
        """Test string representation of movement item"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.50'),
            created_by=self.user,
            updated_by=self.user
        )
        
        expected = f"{self.item.sku_code} (Stock In) x 5.50"
        self.assertEqual(str(movement_item), expected)

    def test_movement_type_choices(self):
        """Test movement type choices"""
        # Test IN movement
        in_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(in_item.movement_type, 'IN')
        self.assertEqual(in_item.get_movement_type_display(), 'Stock In')
        self.assertTrue(in_item.is_inbound)
        
        # Test OUT movement
        out_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.00'),
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(out_item.movement_type, 'OUT')
        self.assertEqual(out_item.get_movement_type_display(), 'Stock Out')
        self.assertTrue(out_item.is_outbound)

    def test_quantity_validation_comprehensive(self):
        """Test comprehensive quantity validation"""
        # Test None quantity
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=None,
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test zero quantity
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('0.00'),
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test negative quantity
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('-5.00'),
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test too many decimal places
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.123'),
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test maximum quantity exceeded
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('1000000.00'),
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

    def test_lot_number_validation(self):
        """Test lot number validation rules"""
        # Test invalid characters
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                lot_number='LOT@2025#001',
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test too long lot number
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                lot_number='A' * 65,  # 65 characters
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test valid lot numbers
        valid_lot_numbers = ['LOT2025001', 'BATCH-123', 'LOT_ABC/001']
        for lot_number in valid_lot_numbers:
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                lot_number=lot_number,
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()  # Should not raise

    def test_expiry_date_validation_extended(self):
        """Test extended expiry date validation"""
        # Test past expiry date
        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                expiry_date=past_date,
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

        # Test far future expiry date (more than 50 years)
        far_future_date = date.today().replace(year=date.today().year + 51)
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                expiry_date=far_future_date,
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

    def test_duplicate_item_validation(self):
        """Test duplicate item prevention"""
        # Create first movement item
        StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate
        with self.assertRaises(ValidationError):
            duplicate_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('5.00'),
                lot_number='LOT001',
                created_by=self.user,
                updated_by=self.user
            )
            duplicate_item.full_clean()

    def test_movement_type_consistency(self):
        """Test movement type consistency with parent movement"""
        # Test missing stock movement
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=None,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

    def test_inactive_item_validation(self):
        """Test that inactive items cannot be moved"""
        # Create inactive item
        inactive_item = ItemSKU.objects.create(
            sku_code='INACTIVE001',
            name='Inactive Item',
            category=self.category,
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.INACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=inactive_item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

    def test_note_length_validation(self):
        """Test note field length validation"""
        # Test valid note
        valid_note = "A" * 500  # Exactly 500 characters
        movement_item = StockMovementItem(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            note=valid_note,
            created_by=self.user,
            updated_by=self.user
        )
        movement_item.full_clean()  # Should not raise
        
        # Test too long note
        with self.assertRaises(ValidationError):
            long_note = "A" * 501  # 501 characters
            movement_item = StockMovementItem(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                note=long_note,
                created_by=self.user,
                updated_by=self.user
            )
            movement_item.full_clean()

    def test_unique_constraint(self):
        """Test unique together constraint"""
        # Create first movement item
        StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            StockMovementItem.objects.create(
                stock_movement=self.stock_movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('5.00'),
                lot_number='LOT001',
                created_by=self.user,
                updated_by=self.user
            )

    def test_confirmed_movement_protection(self):
        """Test protection against modifying confirmed movements"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Confirm the stock movement
        self.stock_movement.status = StockMovement.Status.CONFIRMED
        self.stock_movement.save()
        
        # Try to modify - should raise ValidationError
        movement_item.quantity = Decimal('20.00')
        with self.assertRaises(ValidationError):
            movement_item.save()
        
        # Try to delete - should raise ValidationError
        with self.assertRaises(ValidationError):
            movement_item.delete()

    def test_optimistic_locking(self):
        """Test optimistic locking functionality"""
        # Create movement item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get two instances of the same record
        item1 = StockMovementItem.objects.get(pk=movement_item.pk)
        item2 = StockMovementItem.objects.get(pk=movement_item.pk)
        
        # Modify and save first instance
        item1.quantity = Decimal('15.00')
        item1.save()
        
        # Try to modify and save second instance - should fail
        item2.quantity = Decimal('20.00')
        with self.assertRaises(ValidationError):
            item2.save()

    def test_can_modify_property(self):
        """Test can_modify property"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should be modifiable when movement is DRAFT
        self.assertTrue(movement_item.can_modify)
        
        # Should not be modifiable when movement is CONFIRMED
        self.stock_movement.status = StockMovement.Status.CONFIRMED
        self.stock_movement.save()
        movement_item.refresh_from_db()
        self.assertFalse(movement_item.can_modify)

    def test_get_display_name(self):
        """Test get_display_name method"""
        # Test inbound movement
        in_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        expected_in = f"← {self.item.name} (x10.00)"
        self.assertEqual(in_item.get_display_name(), expected_in)
        
        # Test outbound movement
        out_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.00'),
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        
        expected_out = f"→ {self.item.name} (x5.00)"
        self.assertEqual(out_item.get_display_name(), expected_out)

    def test_audit_fields(self):
        """Test audit fields are set correctly"""
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(movement_item.created_by, self.user)
        self.assertEqual(movement_item.updated_by, self.user)
        self.assertIsNotNone(movement_item.created_at)
        self.assertIsNotNone(movement_item.updated_at)
        self.assertEqual(movement_item.version, 0)

    def test_model_ordering(self):
        """Test model default ordering"""
        # Create multiple movement items
        item1 = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another item with different SKU
        item2_sku = ItemSKU.objects.create(
            sku_code='TEST002',
            name='Test Item 2',
            unit='pcs',
            category=self.category,
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        item2 = StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=item2_sku,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.00'),
            lot_number='LOT002',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check ordering (should be by -created_at, then item_sku__sku_code)
        items = list(StockMovementItem.objects.all())
        self.assertEqual(items[0], item2)  # More recent
        self.assertEqual(items[1], item1)
