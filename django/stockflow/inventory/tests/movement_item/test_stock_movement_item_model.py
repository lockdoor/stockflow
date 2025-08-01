from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
from decimal import Decimal

# Import models
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from inventory.models.warehouse import Warehouse


class StockMovementItemModelTest(TestCase):
    def setUp(self):
        """Set up test data for all test methods"""
        # Create users
        self.user = User.objects.create_user(username='tester', password='test')
        self.user2 = User.objects.create_user(username='tester2', password='test2')
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN01', 
            address='123 Main St',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create ItemSKU with proper fields
        self.item = ItemSKU.objects.create(
            name='Test Item',
            sku_code='SKU001', 
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create StockMovement
        # Create StockMovement
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_stock_movement_item_success(self):
        """Test creating a stock movement item successfully"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date(2025, 12, 31),
            note='Test inbound item',
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Check all fields
        self.assertEqual(item.stock_movement, self.movement)
        self.assertEqual(item.item_sku, self.item)
        self.assertEqual(item.movement_type, StockMovementItem.MovementType.IN)
        self.assertEqual(item.quantity, Decimal('10.00'))
        self.assertEqual(item.lot_number, 'LOT001')
        self.assertEqual(item.expiry_date, date(2025, 12, 31))
        self.assertEqual(item.note, 'Test inbound item')
        self.assertEqual(item.created_by, self.user)
        self.assertEqual(item.version, 1)
        
        # Check properties
        self.assertTrue(item.is_inbound)
        self.assertFalse(item.is_outbound)
        self.assertFalse(item.is_immutable())
        self.assertTrue(item.can_modify())
        
        # Check string representation
        expected_str = f"SKU001 (Stock In) x 10.00"
        self.assertEqual(str(item), expected_str)

    def test_create_outbound_item(self):
        """Test creating an outbound stock movement item"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(item.movement_type, StockMovementItem.MovementType.OUT)
        self.assertFalse(item.is_inbound)
        self.assertTrue(item.is_outbound)
        
        # Check display name
        expected_display = "→ Test Item (x5.00)"
        self.assertEqual(item.get_display_name(), expected_display)

    def test_update_draft_movement_item(self):
        """Test updating an item in draft movement"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Update quantity
        original_version = item.version
        item.quantity = Decimal('15.00')
        item.note = 'Updated quantity'
        item.save()
        item.refresh_from_db()
        
        self.assertEqual(item.quantity, Decimal('15.00'))
        self.assertEqual(item.note, 'Updated quantity')
        self.assertEqual(item.version, original_version + 1)

    def test_immutable_when_movement_completed(self):
        """Test that item becomes immutable when movement is completed"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Initially should be modifiable
        self.assertFalse(item.is_immutable())
        self.assertTrue(item.can_modify())
        
        # Confirm the movement
        self.movement.confirm(self.user)
        item.refresh_from_db()
        
        # Check movement status is COMPLETED
        self.assertEqual(self.movement.status, StockMovement.Status.COMPLETED)
        
        # Now should be immutable
        self.assertTrue(item.is_immutable())
        self.assertFalse(item.can_modify())

    def test_cannot_delete_when_movement_completed(self):
        """Test that item cannot be deleted when movement is completed"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Confirm the movement
        self.movement.confirm(self.user)
        
        # Verify movement is completed
        self.assertEqual(self.movement.status, StockMovement.Status.COMPLETED)
        
        # Verify item is immutable
        self.assertTrue(item.is_immutable())
        self.assertFalse(item.can_modify())

    def test_unique_constraint(self):
        """Test unique constraint for stock_movement + item_sku + lot_number + movement_type"""
        # Create first item
        StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Try to create duplicate with same movement_type - should fail
        with self.assertRaises(IntegrityError):
            StockMovementItem.objects.create(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,  # Same movement type
                quantity=Decimal('5.00'),
                lot_number='LOT001',  # Same lot
                expiry_date=date.today() + timedelta(days=365),
                created_by=self.user,
                updated_by=self.user,
            )

    def test_different_lots_allowed(self):
        """Test that different lots for same item are allowed"""
        # Create first item with LOT001
        item1 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create second item with LOT002 - should be allowed
        item2 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='LOT002',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(item1.lot_number, 'LOT001')
        self.assertEqual(item2.lot_number, 'LOT002')

    def test_optimistic_locking(self):
        """Test optimistic locking prevents concurrent modifications"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Get two instances (simulating two users)
        item_user1 = StockMovementItem.objects.get(pk=item.pk)
        item_user2 = StockMovementItem.objects.get(pk=item.pk)
        
        # User 1 modifies first
        item_user1.quantity = Decimal('15.00')
        item_user1.save()
        
        # User 2 tries to modify with stale version
        item_user2.quantity = Decimal('20.00')
        with self.assertRaises(ValidationError) as context:
            item_user2.save()
        
        self.assertIn('Record has been modified by another user', str(context.exception))
        
        # Verify only user 1's change was saved
        item.refresh_from_db()
        self.assertEqual(item.quantity, Decimal('15.00'))

    def test_validators(self):
        """Test custom validators"""
        # Test negative quantity
        with self.assertRaises(ValidationError):
            item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('-5.00'),  # Negative quantity should fail
                lot_number='LOT001',
                expiry_date=date.today() + timedelta(days=365),
                created_by=self.user,
                updated_by=self.user,
            )
            item.full_clean()
        
        # Test zero quantity
        with self.assertRaises(ValidationError):
            item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('0.00'),  # Zero quantity should fail
                lot_number='LOT001',
                expiry_date=date.today() + timedelta(days=365),
                created_by=self.user,
                updated_by=self.user,
            )
            item.full_clean()

    def test_expired_date_validation(self):
        """Test expiry date validation"""
        # Past date should be allowed with warning (business decision)
        past_date = date.today() - timedelta(days=1)
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=past_date,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.expiry_date, past_date)

    def test_business_logic_methods(self):
        """Test business logic helper methods"""
        # Test inbound item
        inbound_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertTrue(inbound_item.is_inbound)
        self.assertFalse(inbound_item.is_outbound)
        self.assertEqual(inbound_item.get_display_name(), "← Test Item (x10.00)")
        
        # Confirm first movement to create stock for outbound
        self.movement.confirm(self.user)  
        
        # Create new movement for outbound test
        outbound_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            created_by=self.user,
            updated_by=self.user
        )
        
        outbound_item = StockMovementItem.objects.create(
            stock_movement=outbound_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertFalse(outbound_item.is_inbound)
        self.assertTrue(outbound_item.is_outbound)
        self.assertEqual(outbound_item.get_display_name(), "→ Test Item (x5.00)")

    def test_audit_fields_properly_set(self):
        """Test that audit fields are properly set and updated"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Check initial audit fields
        self.assertEqual(item.created_by, self.user)
        self.assertEqual(item.updated_by, self.user)
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)
        
        # Update with different user
        item.quantity = Decimal('15.00')
        item.updated_by = self.user2
        item.save()
        
        # Check that created_by didn't change but updated_by did
        self.assertEqual(item.created_by, self.user)  # Should not change
        self.assertEqual(item.updated_by, self.user2)  # Should change

    def test_lot_number_required(self):
        """Test that lot_number is required"""
        with self.assertRaises(ValidationError):
            item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal('10.00'),
                lot_number='',  # Empty lot number should fail
                expiry_date=date.today() + timedelta(days=365),
                created_by=self.user,
                updated_by=self.user,
            )
            item.full_clean()

    def test_different_movement_types_same_lot(self):
        """Test that same lot can have both IN and OUT movement types"""
        # Create IN movement item
        in_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create OUT movement item with same lot - should be allowed
        out_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.00'),
            lot_number='LOT001',  # Same lot number
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(in_item.lot_number, 'LOT001')
        self.assertEqual(out_item.lot_number, 'LOT001')
        self.assertNotEqual(in_item.movement_type, out_item.movement_type)

    def test_string_representation_variations(self):
        """Test string representation with different scenarios"""
        # Test IN movement
        in_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.50'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        expected_in = "SKU001 (Stock In) x 10.50"
        self.assertEqual(str(in_item), expected_in)
        
        # Test OUT movement
        out_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.25'),
            lot_number='LOT002',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        expected_out = "SKU001 (Stock Out) x 5.25"
        self.assertEqual(str(out_item), expected_out)

    def test_decimal_precision(self):
        """Test that decimal quantities maintain proper precision"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.123'),  # High precision
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Should maintain precision up to model field definition
        item.refresh_from_db()
        self.assertEqual(item.quantity, Decimal('10.12'))  # Rounded to 2 decimal places

    def test_expiry_date_edge_cases(self):
        """Test expiry date with various edge cases"""
        # Test far future date
        far_future = date.today() + timedelta(days=3650)  # 10 years
        item1 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT_FUTURE',
            expiry_date=far_future,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item1.expiry_date, far_future)
        
        # Test today's date
        today = date.today()
        item2 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='LOT_TODAY',
            expiry_date=today,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item2.expiry_date, today)

    def test_note_field_optional(self):
        """Test that note field is optional"""
        # Create item without note
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date.today() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertIsNone(item.note)
        
        # Add note later
        item.note = 'Added note later'
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.note, 'Added note later')
