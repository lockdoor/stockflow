"""
Tests for Stock Movement Item Lot Validator

Tests the lot number generation and uniqueness validation functionality.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU
from inventory.validators.stock_movement_item_validators import StockMovementItemLotValidator


class StockMovementItemLotValidatorTest(TestCase):
    """Test cases for StockMovementItemLotValidator"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            name='Test Item',
            sku_code='SKU001',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_auto_generate_lot_number_when_empty(self):
        """Test that lot number is auto-generated when not provided"""
        movement_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            # lot_number not provided
        )
        
        validator = StockMovementItemLotValidator(movement_item)
        error = validator.validate()
        
        # Should not have error
        self.assertIsNone(error)
        
        # Should have generated lot number
        self.assertIsNotNone(movement_item.lot_number)
        self.assertTrue(len(movement_item.lot_number) > 0)
        
        # Should follow format: YYYYMMDD-HHMMSS-XXXXXXXX
        import re
        pattern = r'^\d{8}-\d{6}-[A-Z0-9]{8}$'
        self.assertTrue(re.match(pattern, movement_item.lot_number))
    
    def test_auto_generate_lot_number_when_none(self):
        """Test that lot number is auto-generated when explicitly None"""
        movement_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number=None
        )
        
        validator = StockMovementItemLotValidator(movement_item)
        error = validator.validate()
        
        self.assertIsNone(error)
        self.assertIsNotNone(movement_item.lot_number)
    
    def test_auto_generate_lot_number_when_empty_string(self):
        """Test that lot number is auto-generated when empty string"""
        movement_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number=''
        )
        
        validator = StockMovementItemLotValidator(movement_item)
        error = validator.validate()
        
        self.assertIsNone(error)
        self.assertIsNotNone(movement_item.lot_number)
        self.assertTrue(len(movement_item.lot_number) > 0)
    
    def test_keep_existing_lot_number(self):
        """Test that existing lot number is kept when provided"""
        custom_lot = 'CUSTOM-LOT-001'
        movement_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number=custom_lot
        )
        
        validator = StockMovementItemLotValidator(movement_item)
        error = validator.validate()
        
        self.assertIsNone(error)
        self.assertEqual(movement_item.lot_number, custom_lot)
    
    def test_lot_number_uniqueness_validation(self):
        """Test that duplicate lot numbers are rejected"""
        # Create first item with specific lot number
        first_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='DUPLICATE-LOT',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create second item with same lot number
        second_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='DUPLICATE-LOT'
        )
        
        validator = StockMovementItemLotValidator(second_item)
        error = validator.validate()
        
        self.assertIsNotNone(error)
        self.assertIn("already exists", error)
        self.assertIn("DUPLICATE-LOT", error)
    
    def test_lot_number_uniqueness_different_movement_type_allowed(self):
        """Test that same lot number is allowed for different movement types"""
        # Create first item with IN movement
        first_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='SAME-LOT',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create second item with OUT movement (should be allowed)
        second_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('3.00'),
            lot_number='SAME-LOT'
        )
        
        validator = StockMovementItemLotValidator(second_item)
        error = validator.validate()
        
        self.assertIsNone(error)
    
    def test_lot_number_uniqueness_different_item_allowed(self):
        """Test that same lot number is allowed for different items"""
        # Create another item
        other_item = ItemSKU.objects.create(
            name='Other Item',
            sku_code='SKU002',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create first item
        first_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='SAME-LOT',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create second item with different SKU (should be allowed)
        second_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=other_item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='SAME-LOT'
        )
        
        validator = StockMovementItemLotValidator(second_item)
        error = validator.validate()
        
        self.assertIsNone(error)
    
    def test_lot_number_uniqueness_different_movement_allowed(self):
        """Test that same lot number is allowed in different movements"""
        # Create another warehouse for the second movement
        other_warehouse = Warehouse.objects.create(
            name='Other Warehouse',
            code='TEST02',
            address='456 Other St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another movement in different warehouse
        other_movement = StockMovement.objects.create(
            warehouse=other_warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create first item in first movement
        first_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='SAME-LOT',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create second item in different movement (should be allowed)
        second_item = StockMovementItem(
            stock_movement=other_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='SAME-LOT'
        )
        
        validator = StockMovementItemLotValidator(second_item)
        error = validator.validate()
        
        self.assertIsNone(error)
    
    def test_lot_number_format_validation(self):
        """Test lot number format validation"""
        invalid_lots = [
            'LOT WITH SPACES',  # spaces not allowed
            'LOT@SPECIAL',      # @ not allowed
            'LOT#123',          # # not allowed
            'LOT$456',          # $ not allowed
            'LOT%789',          # % not allowed
        ]
        
        for invalid_lot in invalid_lots:
            movement_item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                lot_number=invalid_lot
            )
            
            validator = StockMovementItemLotValidator(movement_item)
            error = validator.validate()
            
            self.assertIsNotNone(error, f"Should reject invalid lot: {invalid_lot}")
            self.assertIn("can only contain", error)
    
    def test_lot_number_valid_format(self):
        """Test valid lot number formats"""
        valid_lots = [
            'LOT123',
            'LOT-123',
            'LOT_123',
            'LOT/123',
            'ABC-DEF_123/456',
            '2025-01-01-BATCH',
        ]
        
        for valid_lot in valid_lots:
            movement_item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                lot_number=valid_lot
            )
            
            validator = StockMovementItemLotValidator(movement_item)
            error = validator.validate()
            
            self.assertIsNone(error, f"Should accept valid lot: {valid_lot}")
    
    def test_lot_number_length_validation(self):
        """Test lot number length validation"""
        # Test maximum length (64 characters)
        long_lot = 'A' * 65  # 65 characters
        movement_item = StockMovementItem(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number=long_lot
        )
        
        validator = StockMovementItemLotValidator(movement_item)
        error = validator.validate()
        
        self.assertIsNotNone(error)
        self.assertIn("cannot exceed 64 characters", error)
        
        # Test valid length (64 characters)
        valid_lot = 'A' * 64  # exactly 64 characters
        movement_item.lot_number = valid_lot
        
        error = validator.validate()
        self.assertIsNone(error)
    
    def test_auto_generated_lot_uniqueness(self):
        """Test that auto-generated lot numbers are unique"""
        # Create multiple items without lot numbers
        items = []
        for i in range(5):
            movement_item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                # No lot_number provided
            )
            
            validator = StockMovementItemLotValidator(movement_item)
            error = validator.validate()
            
            self.assertIsNone(error)
            self.assertIsNotNone(movement_item.lot_number)
            items.append(movement_item)
        
        # Check that all generated lot numbers are unique
        lot_numbers = [item.lot_number for item in items]
        unique_lots = set(lot_numbers)
        
        self.assertEqual(len(lot_numbers), len(unique_lots), 
                        "All auto-generated lot numbers should be unique")
    
    def test_updating_existing_item_preserves_lot(self):
        """Test that updating existing item doesn't trigger uniqueness error"""
        # Create item
        movement_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='UPDATE-TEST',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update same item (should not trigger uniqueness error)
        movement_item.quantity = Decimal('15.00')
        
        validator = StockMovementItemLotValidator(movement_item)
        error = validator.validate()
        
        self.assertIsNone(error)
        self.assertEqual(movement_item.lot_number, 'UPDATE-TEST')
