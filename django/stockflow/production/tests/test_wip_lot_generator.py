"""
Tests for WIP Return Lot Number Generation

Test cases covering lot number generation, validation, and WIP material returns.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from catalog.models import ItemSKU
from inventory.models import StockMovement, StockMovementItem, Warehouse
from production.models import ProductionOrder, WIPStockMovement
from production.utils.wip_lot_generator import (
    generate_wip_return_lot_number,
    validate_wip_return_lot_format,
    extract_production_order_from_lot,
    get_wip_return_lots_for_production_order
)
from tests.factories import WarehouseFactory, ItemFactory, ProductionOrderFactory

User = get_user_model()


class WIPLotGeneratorTestCase(TestCase):
    """Test cases for WIP lot number generation utilities"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test warehouse
        self.warehouse = WarehouseFactory(created_by=self.user, updated_by=self.user)
        
        # Create test item SKU  
        self.item_sku = ItemFactory(created_by=self.user, updated_by=self.user)
        
        # Create test production order
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_generate_lot_number_format(self):
        """Test lot number follows correct format"""
        lot_number = generate_wip_return_lot_number(123)
        
        # Should match pattern: WIP-PO123-RET-YYYYMMDDHHMMSS
        self.assertTrue(lot_number.startswith('WIP-PO123-RET-'))
        self.assertTrue(validate_wip_return_lot_format(lot_number))
        
        # Check length (WIP-PO + 3 digits + -RET- + 14 digits = 25 characters minimum)
        self.assertGreaterEqual(len(lot_number), 25)

    def test_generate_lot_number_with_padding(self):
        """Test lot number uses proper padding for production order ID"""
        lot_number = generate_wip_return_lot_number(1)
        
        # Should pad to 3 digits: WIP-PO001-RET-...
        self.assertTrue(lot_number.startswith('WIP-PO001-RET-'))
        
        lot_number = generate_wip_return_lot_number(99)
        self.assertTrue(lot_number.startswith('WIP-PO099-RET-'))
        
        lot_number = generate_wip_return_lot_number(1000)
        self.assertTrue(lot_number.startswith('WIP-PO1000-RET-'))

    def test_generate_lot_number_uniqueness(self):
        """Test lot number uniqueness handling"""
        production_order_id = 123
        
        # Generate first lot number
        lot1 = generate_wip_return_lot_number(production_order_id, self.item_sku.id)
        
        # Create a StockMovementItem with this lot number
        stock_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=self.production_order.id,
            created_by=self.user,
            updated_by=self.user
        )
        
        StockMovementItem.objects.create(
            stock_movement=stock_movement,
            item_sku=self.item_sku,
            quantity=Decimal('10.00'),
            movement_type='IN',
            lot_number=lot1,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Generate second lot number with different item (should be different due to item_sku_id)
        item2 = ItemFactory(created_by=self.user, updated_by=self.user)
        lot2 = generate_wip_return_lot_number(production_order_id, item2.id)
        
        # Should be different due to different item_sku_id
        self.assertNotEqual(lot1, lot2)
        
        # Both should be valid format (relaxed validation for new format)
        self.assertTrue(lot1.startswith('WIP-PO123-RET-'))
        self.assertTrue(lot2.startswith('WIP-PO123-RET-'))

    def test_validate_lot_format_valid_cases(self):
        """Test validation of valid WIP return lot formats"""
        valid_lots = [
            'WIP-PO001-RET-20250910143022',
            'WIP-PO999-RET-20250910143022',
            'WIP-PO1000-RET-20250910143022',
            'WIP-PO001-RET-20250910143022-01',     # With counter
            'WIP-PO001-RET-20250910143022-99',     # With counter
            'WIP-PO001-RET-202509101430221234',    # With microseconds
            'WIP-PO001-RET-20250910143022-ITM456', # With item ID
            'WIP-PO001-RET-20250910143022-ITM456-01', # With item ID and counter
        ]
        
        for lot in valid_lots:
            with self.subTest(lot=lot):
                self.assertTrue(validate_wip_return_lot_format(lot))

    def test_validate_lot_format_invalid_cases(self):
        """Test validation rejects invalid lot formats"""
        invalid_lots = [
            'REGULAR-LOT-001',
            'WIP-001-RET-20250910143022',  # Missing PO prefix
            'WIP-PO1-RET-20250910',        # Short timestamp
            'WIP-PO001-RET',               # Missing timestamp
            'WIP-PO001-20250910143022',    # Missing RET
            '',                            # Empty string
            'WIP-PO-RET-20250910143022',   # Missing PO number
        ]
        
        for lot in invalid_lots:
            with self.subTest(lot=lot):
                self.assertFalse(validate_wip_return_lot_format(lot))

    def test_extract_production_order_from_lot(self):
        """Test extraction of production order ID from lot number"""
        test_cases = [
            ('WIP-PO001-RET-20250910143022', 1),
            ('WIP-PO123-RET-20250910143022', 123),
            ('WIP-PO999-RET-20250910143022', 999),
            ('WIP-PO1000-RET-20250910143022', 1000),
            ('WIP-PO001-RET-20250910143022-01', 1),     # With counter
            ('WIP-PO123-RET-20250910143022-ITM456', 123), # With item ID
            ('WIP-PO123-RET-20250910143022-ITM456-01', 123), # With item ID and counter
            ('REGULAR-LOT-001', None),                  # Invalid format
            ('', None),                                 # Empty string
        ]
        
        for lot, expected_po_id in test_cases:
            with self.subTest(lot=lot):
                result = extract_production_order_from_lot(lot)
                self.assertEqual(result, expected_po_id)

    def test_get_wip_return_lots_for_production_order(self):
        """Test retrieval of WIP return lots for production order"""
        production_order_id = self.production_order.id
        
        # Initially should be empty
        lots = get_wip_return_lots_for_production_order(production_order_id)
        self.assertEqual(len(lots), 0)
        
        # Create some WIP return stock movements
        stock_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=production_order_id,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create multiple items with WIP return lot numbers
        lot1 = generate_wip_return_lot_number(production_order_id)
        lot2 = generate_wip_return_lot_number(production_order_id)
        
        StockMovementItem.objects.create(
            stock_movement=stock_movement,
            item_sku=self.item_sku,
            quantity=Decimal('10.00'),
            movement_type='IN',
            lot_number=lot1,
            created_by=self.user,
            updated_by=self.user
        )
        
        StockMovementItem.objects.create(
            stock_movement=stock_movement,
            item_sku=self.item_sku,
            quantity=Decimal('5.00'),
            movement_type='IN',
            lot_number=lot2,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should find both lots
        lots = get_wip_return_lots_for_production_order(production_order_id)
        self.assertEqual(len(lots), 2)
        self.assertIn(lot1, lots)
        self.assertIn(lot2, lots)
        
        # Should not include lots from other production orders
        other_po_lot = generate_wip_return_lot_number(999)
        StockMovementItem.objects.create(
            stock_movement=stock_movement,
            item_sku=self.item_sku,
            quantity=Decimal('3.00'),
            movement_type='IN',
            lot_number=other_po_lot,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should still only find lots for our production order
        lots = get_wip_return_lots_for_production_order(production_order_id)
        self.assertEqual(len(lots), 2)
        self.assertNotIn(other_po_lot, lots)


class WIPReturnIntegrationTestCase(TestCase):
    """Integration tests for WIP material return with lot generation"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test warehouse
        self.warehouse = WarehouseFactory(created_by=self.user, updated_by=self.user)
        
        # Create test item SKU
        self.item_sku = ItemFactory(created_by=self.user, updated_by=self.user)
        
        # Create test production order
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Set status to CANCELLED to allow WIP returns
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.CANCELLED
        )
        self.production_order.refresh_from_db()
        
        # Create WIP stock movements (materials in WIP)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item_sku,
            quantity=Decimal('15.00'),
            note='Test WIP material',
            created_by=self.user,
            updated_by=self.user
        )

    def test_bulk_return_creates_correct_lots(self):
        """Test bulk return generates proper lot numbers"""
        # Get WIP materials summary
        wip_materials = self.production_order.get_wip_materials_summary()
        self.assertEqual(len(wip_materials), 1)
        self.assertEqual(wip_materials[0]['balance'], Decimal('15.00'))
        
        # Simulate bulk return process
        from production.utils.wip_lot_generator import generate_wip_return_lot_number
        
        stock_movement = StockMovement.objects.create(
            warehouse=self.production_order.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=self.production_order.id,
            note=f"Bulk return of WIP materials from cancelled production order #{self.production_order.id}",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create movement items with generated lot numbers
        for material in wip_materials:
            if material['balance'] > 0:
                lot_number = generate_wip_return_lot_number(
                    production_order_id=self.production_order.id,
                    item_sku_id=material['item_sku'].id
                )
                
                StockMovementItem.objects.create(
                    stock_movement=stock_movement,
                    item_sku=material['item_sku'],
                    quantity=material['balance'],
                    movement_type='IN',
                    lot_number=lot_number,
                    expiry_date=None,
                    note=f"Return from Production Order #{self.production_order.id}",
                    created_by=self.user,
                    updated_by=self.user
                )
        
        # Verify stock movement items created correctly
        items = stock_movement.movement_items.all()
        self.assertEqual(items.count(), 1)
        
        item = items.first()
        self.assertEqual(item.item_sku, self.item_sku)
        self.assertEqual(item.quantity, Decimal('15.00'))
        self.assertEqual(item.movement_type, 'IN')
        self.assertIsNotNone(item.lot_number)
        self.assertTrue(validate_wip_return_lot_format(item.lot_number))
        self.assertIsNone(item.expiry_date)
        
        # Verify lot number contains production order ID
        po_id = extract_production_order_from_lot(item.lot_number)
        self.assertEqual(po_id, self.production_order.id)

    def test_multiple_materials_get_different_lots(self):
        """Test multiple materials get different lot numbers"""
        # Create another item SKU
        item_sku2 = ItemFactory(created_by=self.user, updated_by=self.user)
        
        # Create WIP for second item
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=item_sku2,
            quantity=Decimal('8.00'),
            note='Test WIP material 2',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get WIP materials summary
        wip_materials = self.production_order.get_wip_materials_summary()
        self.assertEqual(len(wip_materials), 2)
        
        # Generate lot numbers for both materials
        lot_numbers = []
        for material in wip_materials:
            lot_number = generate_wip_return_lot_number(
                production_order_id=self.production_order.id,
                item_sku_id=material['item_sku'].id
            )
            lot_numbers.append(lot_number)
        
        # Should be different lot numbers
        self.assertEqual(len(set(lot_numbers)), 2)
        
        # Both should be valid format
        for lot in lot_numbers:
            self.assertTrue(validate_wip_return_lot_format(lot))
            self.assertEqual(extract_production_order_from_lot(lot), self.production_order.id)

    def test_bulk_return_creates_wip_movements(self):
        """Test bulk return creates corresponding WIP stock movements"""
        # Get WIP materials summary
        wip_materials = self.production_order.get_wip_materials_summary()
        self.assertEqual(len(wip_materials), 1)
        self.assertEqual(wip_materials[0]['balance'], Decimal('15.00'))
        
        # Simulate bulk return process with WIP movements
        from production.utils.wip_lot_generator import generate_wip_return_lot_number
        
        stock_movement = StockMovement.objects.create(
            warehouse=self.production_order.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=self.production_order.id,
            note=f"Bulk return of WIP materials from cancelled production order #{self.production_order.id}",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create movement items with generated lot numbers
        for material in wip_materials:
            if material['balance'] > 0:
                lot_number = generate_wip_return_lot_number(
                    production_order_id=self.production_order.id,
                    item_sku_id=material['item_sku'].id
                )
                
                StockMovementItem.objects.create(
                    stock_movement=stock_movement,
                    item_sku=material['item_sku'],
                    quantity=material['balance'],
                    movement_type='IN',
                    lot_number=lot_number,
                    expiry_date=None,
                    note=f"Return from Production Order #{self.production_order.id}",
                    created_by=self.user,
                    updated_by=self.user
                )
                
                # Create corresponding WIP stock movement for return
                WIPStockMovement.objects.create(
                    production_order=self.production_order,
                    source_stock_movement=stock_movement,
                    movement_type=WIPStockMovement.MovementType.RETURN,
                    item_sku=material['item_sku'],
                    quantity=material['balance'],
                    note=f"Return WIP materials to inventory via stock movement #{stock_movement.id}",
                    created_by=self.user,
                    updated_by=self.user
                )
        
        # Verify WIP stock movements were created
        wip_returns = WIPStockMovement.objects.filter(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.RETURN
        )
        self.assertEqual(wip_returns.count(), 1)
        
        wip_return = wip_returns.first()
        self.assertEqual(wip_return.item_sku, self.item_sku)
        self.assertEqual(wip_return.quantity, Decimal('15.00'))
        self.assertEqual(wip_return.source_stock_movement, stock_movement)
        self.assertEqual(wip_return.movement_type, WIPStockMovement.MovementType.RETURN)
        
        # Verify WIP balance is now zero
        new_balance = WIPStockMovement.get_wip_balance(self.production_order, self.item_sku)
        self.assertEqual(new_balance, Decimal('0.00'))
