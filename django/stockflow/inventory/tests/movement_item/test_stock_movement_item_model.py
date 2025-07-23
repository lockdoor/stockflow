from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from catalog.models.item import ItemSKU
from inventory.models.warehouse import Warehouse


class StockMovementItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='test')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN01', 
            address='123 Main St',
            created_by=self.user,
            updated_by=self.user
        )
        self.item = ItemSKU.objects.create(
            name='Test Item',
            sku_code='SKU001', 
            unit='pcs',
            created_by=self.user,
            updated_by=self.user
        )
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
            quantity=10,
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
        self.assertEqual(item.quantity, 10)
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
        expected_str = f"SKU001 (Stock In) x 10"
        self.assertEqual(str(item), expected_str)

    def test_create_outbound_item(self):
        """Test creating an outbound stock movement item"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=5,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertEqual(item.movement_type, StockMovementItem.MovementType.OUT)
        self.assertFalse(item.is_inbound)
        self.assertTrue(item.is_outbound)
        
        # Check display name
        expected_display = "→ Test Item (x5)"
        self.assertEqual(item.get_display_name(), expected_display)

    def test_update_draft_movement_item(self):
        """Test updating an item in draft movement"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=10,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Update quantity
        original_version = item.version
        item.quantity = 15
        item.note = 'Updated quantity'
        item.save()
        item.refresh_from_db()
        
        self.assertEqual(item.quantity, 15)
        self.assertEqual(item.note, 'Updated quantity')
        self.assertEqual(item.version, original_version + 1)

    def test_immutable_when_movement_confirmed(self):
        """Test that item becomes immutable when movement is confirmed"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=10,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Initially should be modifiable
        self.assertFalse(item.is_immutable())
        self.assertTrue(item.can_modify())
        
        # Confirm the movement
        self.movement.confirm(self.user)
        item.refresh_from_db()
        
        # Now should be immutable
        self.assertTrue(item.is_immutable())
        self.assertFalse(item.can_modify())
        
        # Try to modify - should fail
        item.quantity = 20
        with self.assertRaises(ValidationError) as context:
            item.save()
        
        self.assertIn('Cannot modify items in confirmed stock movements', str(context.exception))

    def test_cannot_delete_when_movement_confirmed(self):
        """Test that item cannot be deleted when movement is confirmed"""
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=10,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Confirm the movement
        self.movement.confirm(self.user)
        
        # Try to delete - should fail
        with self.assertRaises(ValidationError) as context:
            item.delete()
        
        self.assertIn('Cannot modify items in confirmed stock movements', str(context.exception))

    def test_unique_constraint(self):
        """Test unique constraint for stock_movement + item_sku + lot_number + movement_type"""
        # Create first item
        StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=10,
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Try to create duplicate with same movement_type - should fail
        with self.assertRaises(IntegrityError):
            StockMovementItem.objects.create(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,  # Same movement type
                quantity=5,
                lot_number='LOT001',  # Same lot
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
            quantity=10,
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create second item with LOT002 - should be allowed
        item2 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=5,
            lot_number='LOT002',
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
            quantity=10,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Get two instances (simulating two users)
        item_user1 = StockMovementItem.objects.get(pk=item.pk)
        item_user2 = StockMovementItem.objects.get(pk=item.pk)
        
        # User 1 modifies first
        item_user1.quantity = 15
        item_user1.save()
        
        # User 2 tries to modify with stale version
        item_user2.quantity = 20
        with self.assertRaises(ValidationError) as context:
            item_user2.save()
        
        self.assertIn('Record has been modified by another user', str(context.exception))
        
        # Verify only user 1's change was saved
        item.refresh_from_db()
        self.assertEqual(item.quantity, 15)

    def test_validators(self):
        """Test custom validators"""
        # Test negative quantity
        with self.assertRaises(ValidationError):
            item = StockMovementItem(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=-5,  # Negative quantity should fail
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
                quantity=0,  # Zero quantity should fail
                created_by=self.user,
                updated_by=self.user,
            )
            item.full_clean()

    def test_expired_date_validation(self):
        """Test expiry date validation"""
        from datetime import date, timedelta
        
        # Past date should be allowed with warning (business decision)
        past_date = date.today() - timedelta(days=1)
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=10,
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
            quantity=10,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertTrue(inbound_item.is_inbound)
        self.assertFalse(inbound_item.is_outbound)
        self.assertEqual(inbound_item.get_display_name(), "← Test Item (x10)")
        
        # Test outbound item
        self.movement.confirm(self.user)  # Confirm first movement
        
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
            quantity=5,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.assertFalse(outbound_item.is_inbound)
        self.assertTrue(outbound_item.is_outbound)
        self.assertEqual(outbound_item.get_display_name(), "→ Test Item (x5)")
