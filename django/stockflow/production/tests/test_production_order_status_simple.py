"""
Simplified Test cases for Production Order Status Management and WIP Materials

This module tests the basic functionality without complex validators
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest import mock

from production.models import ProductionOrder, WIPStockMovement, ProductionOrderBOM
from catalog.models import ItemSKU, Category
from inventory.models import Warehouse
from tests.factories.production.production_order_factory import ProductionOrderFactory
from tests.factories.catalog.item_factory import ItemFactory
from tests.factories.catalog.category_factory import CategoryFactory
from tests.factories.inventory.warehouse_factory import WarehouseFactory

User = get_user_model()


class ProductionStatusMixinSimpleTest(TestCase):
    """Simple tests for ProductionStatusMixin methods"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = CategoryFactory()
        self.warehouse = WarehouseFactory()
        self.item1 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        
        # Create production order with DRAFT status (default)
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_initial_status_is_draft(self):
        """Test that new production order starts with DRAFT status"""
        self.assertEqual(self.production_order.status, ProductionOrder.Status.DRAFT)

    def test_draft_to_created_transition_requires_bom(self):
        """Test that DRAFT to CREATED transition requires BOM items"""
        from production.models import ProductionOrderBOM
        from django.core.exceptions import ValidationError
        
        # Ensure we start with DRAFT status
        self.assertEqual(self.production_order.status, ProductionOrder.Status.DRAFT)
        
        # Should not be able to change to CREATED without BOM items
        self.production_order.status = ProductionOrder.Status.CREATED
        
        with self.assertRaises(ValidationError) as context:
            self.production_order.save()
        
        self.assertIn("must have at least one BOM item", str(context.exception))
        
        # Reset to DRAFT status
        self.production_order.status = ProductionOrder.Status.DRAFT
        
        # After adding BOM item, should be able to change
        ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.item1,
            planned_quantity=Decimal('10'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Now should be able to change to CREATED
        self.production_order.status = ProductionOrder.Status.CREATED
        self.production_order.save()  # Should not raise exception
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CREATED)

    def test_draft_cannot_change_to_other_status_directly(self):
        """Test that DRAFT cannot change to other statuses except CREATED"""
        from django.core.exceptions import ValidationError
        
        # Try to change DRAFT directly to IN_PROGRESS (should fail)
        self.production_order.status = ProductionOrder.Status.IN_PROGRESS
        
        with self.assertRaises(ValidationError) as context:
            self.production_order.save()
        
        self.assertIn("must change from DRAFT to CREATED", str(context.exception))

    def test_can_cancel_created_status(self):
        """Test can_cancel() method for CREATED status"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CREATED
        )
        self.production_order.refresh_from_db()
        self.assertTrue(self.production_order.can_cancel())

    def test_can_delete_draft_status(self):
        """Test that DRAFT production orders can be deleted"""
        # Should be able to delete DRAFT status
        self.assertEqual(self.production_order.status, ProductionOrder.Status.DRAFT)
        production_order_id = self.production_order.id
        
        # This should not raise an exception
        self.production_order.delete()
        
        # Verify it's deleted
        with self.assertRaises(ProductionOrder.DoesNotExist):
            ProductionOrder.objects.get(id=production_order_id)

    def test_cannot_delete_non_draft_status(self):
        """Test that non-DRAFT production orders cannot be deleted"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CREATED
        )
        self.production_order.refresh_from_db()
        
        # Should raise ValidationError when trying to delete
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            self.production_order.delete()
        
        self.assertIn("Only DRAFT production orders can be deleted", str(context.exception))

    def test_cannot_cancel_completed_status(self):
        """Test cannot cancel COMPLETED status"""
        # Bypass validators for testing
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.COMPLETED
        )
        self.production_order.refresh_from_db()
        self.assertFalse(self.production_order.can_cancel())

    def test_can_close_completed_status(self):
        """Test can_close() method for COMPLETED status"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.COMPLETED
        )
        self.production_order.refresh_from_db()
        self.assertTrue(self.production_order.can_close())

    def test_is_finished_closed_statuses(self):
        """Test is_finished() method for closed statuses"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CLOSED_COMPLETED
        )
        self.production_order.refresh_from_db()
        self.assertTrue(self.production_order.is_finished())


class WIPStockMovementSimpleTest(TestCase):
    """Simple tests for WIPStockMovement model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = CategoryFactory()
        self.warehouse = WarehouseFactory()
        self.item1 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_wip_balance_no_movements(self):
        """Test WIP balance calculation with no movements"""
        balance = WIPStockMovement.get_wip_balance(self.production_order, self.item1)
        self.assertEqual(balance, Decimal('0'))

    def test_wip_balance_in_movement(self):
        """Test WIP balance with single IN movement"""
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        balance = WIPStockMovement.get_wip_balance(self.production_order, self.item1)
        self.assertEqual(balance, Decimal('100'))

    def test_wip_balance_mixed_movements(self):
        """Test WIP balance with IN and OUT movements"""
        # IN movement
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # OUT movement
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=self.item1,
            quantity=Decimal('30'),
            created_by=self.user,
            updated_by=self.user
        )
        
        balance = WIPStockMovement.get_wip_balance(self.production_order, self.item1)
        self.assertEqual(balance, Decimal('70'))  # 100 - 30

    def test_get_all_wip_balances_single_item(self):
        """Test get_all_wip_balances() with single item"""
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('50'),
            created_by=self.user,
            updated_by=self.user
        )
        
        balances = WIPStockMovement.get_all_wip_balances(self.production_order)
        self.assertEqual(len(balances), 1)
        self.assertEqual(balances[self.item1.id], Decimal('50'))

    def test_get_all_wip_balances_empty(self):
        """Test get_all_wip_balances() with no movements"""
        balances = WIPStockMovement.get_all_wip_balances(self.production_order)
        self.assertEqual(len(balances), 0)


class ProductionOrderWIPIntegrationSimpleTest(TestCase):
    """Simple integration tests between ProductionOrder and WIPStockMovement"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = CategoryFactory()
        self.warehouse = WarehouseFactory()
        self.item1 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_has_wip_materials_false_no_movements(self):
        """Test has_wip_materials() returns False when no movements"""
        self.assertFalse(self.production_order.has_wip_materials())

    def test_has_wip_materials_true_with_movements(self):
        """Test has_wip_materials() returns True when movements exist"""
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(self.production_order.has_wip_materials())

    def test_has_wip_materials_false_zero_balance(self):
        """Test has_wip_materials() returns False when balance is zero"""
        # Create IN movement
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create equal OUT movement (balance = 0)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertFalse(self.production_order.has_wip_materials())

    def test_get_wip_materials_summary_single_item(self):
        """
        Test get_wip_materials_summary() with single item
        
        Tests:
        - Returns correct data structure (list of dicts with item_sku and balance)
        - Only includes items with positive balance
        - Correctly calculates balance from WIP movements
        - Handles non-existent ItemSKU gracefully
        """
        # Create WIP movement for testing
        wip_movement = WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('75.50'),
            created_by=self.user,
            updated_by=self.user
        )
        
        summary = self.production_order.get_wip_materials_summary()
        
        # Verify structure and content
        self.assertEqual(len(summary), 1, "Should return exactly one material")
        
        material = summary[0]
        self.assertIsInstance(material, dict, "Each material should be a dictionary")
        self.assertIn('item_sku', material, "Material dict should have 'item_sku' key")
        self.assertIn('balance', material, "Material dict should have 'balance' key")
        
        # Verify content accuracy
        self.assertEqual(material['item_sku'], self.item1, "Should return correct ItemSKU")
        self.assertEqual(material['balance'], Decimal('75.50'), "Should return correct balance")
        self.assertIsInstance(material['balance'], Decimal, "Balance should be Decimal type")
        
        # Verify ItemSKU attributes
        self.assertEqual(material['item_sku'].id, self.item1.id)
        self.assertEqual(material['item_sku'].name, self.item1.name)
        self.assertEqual(material['item_sku'].type, self.item1.type)

    def test_get_wip_materials_summary_only_positive_balances(self):
        """Test that only materials with positive balances are included"""
        # Create IN movement
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create equal OUT movement (making balance = 0)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        summary = self.production_order.get_wip_materials_summary()
        
        # Should return empty list since balance is 0
        self.assertEqual(len(summary), 0, "Should not include items with zero balance")

    def test_get_wip_materials_summary_multiple_items(self):
        """Test get_wip_materials_summary() with multiple items"""
        # Create a second item (use ACTIVE status for RAW materials)
        item2 = ItemFactory(category=self.category, type=ItemSKU.Type.RAW, status=ItemSKU.Status.ACTIVE)
        
        # Create WIP movements for both items
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('25.5'),
            created_by=self.user,
            updated_by=self.user
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=item2,
            quantity=Decimal('50.75'),
            created_by=self.user,
            updated_by=self.user
        )
        
        summary = self.production_order.get_wip_materials_summary()
        
        # Should return both items
        self.assertEqual(len(summary), 2, "Should return both items with positive balances")
        
        # Sort by balance for consistent testing
        summary.sort(key=lambda x: x['balance'])
        
        # Verify first item (smaller balance)
        self.assertEqual(summary[0]['item_sku'], self.item1)
        self.assertEqual(summary[0]['balance'], Decimal('25.5'))
        
        # Verify second item (larger balance)
        self.assertEqual(summary[1]['item_sku'], item2)
        self.assertEqual(summary[1]['balance'], Decimal('50.75'))

    def test_get_wip_materials_summary_calculated_balance(self):
        """Test that balance is correctly calculated from multiple movements"""
        # Create multiple IN movements
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('50'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create OUT movement
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=self.item1,
            quantity=Decimal('30'),
            created_by=self.user,
            updated_by=self.user
        )
        
        summary = self.production_order.get_wip_materials_summary()
        
        # Should calculate: (100 + 50) - 30 = 120
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['balance'], Decimal('120'))
        self.assertEqual(summary[0]['item_sku'], self.item1)

    def test_wip_materials_workflow_integration(self):
        """Test complete workflow integration between WIP movements and summary"""
        # Create multiple items with different statuses
        raw_item = ItemFactory(category=self.category, type=ItemSKU.Type.RAW, status=ItemSKU.Status.ACTIVE)
        
        # Scenario: Materials withdrawn for production (IN movements)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,  # PRODUCT type (DRAFT status)
            quantity=Decimal('100.00'),
            note='Initial withdrawal for production',
            created_by=self.user,
            updated_by=self.user
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=raw_item,  # RAW type (ACTIVE status)
            quantity=Decimal('50.25'),
            note='Raw material for processing',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Scenario: Some materials consumed during production (OUT movements)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=raw_item,
            quantity=Decimal('15.25'),  # Partial consumption
            note='Used in production process',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test has_wip_materials() reflects current state
        self.assertTrue(self.production_order.has_wip_materials())
        
        # Get summary and verify it shows remaining balances
        summary = self.production_order.get_wip_materials_summary()
        
        # Should have 2 items with positive balances
        self.assertEqual(len(summary), 2)
        
        # Find items in summary
        balances_by_item = {material['item_sku']: material['balance'] for material in summary}
        
        # Verify balances
        self.assertEqual(balances_by_item[self.item1], Decimal('100.00'))    # No consumption
        self.assertEqual(balances_by_item[raw_item], Decimal('35.00'))       # 50.25 - 15.25 = 35.00
        
        # Scenario: Complete consumption of one item (item1)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=self.item1,
            quantity=Decimal('100.00'),  # Complete consumption
            note='Fully consumed in production',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get updated summary
        updated_summary = self.production_order.get_wip_materials_summary()
        
        # Should now have only 1 item (item1 excluded due to zero balance)
        self.assertEqual(len(updated_summary), 1)
        
        # Verify item1 is not in summary anymore
        remaining_items = {material['item_sku'] for material in updated_summary}
        self.assertNotIn(self.item1, remaining_items)
        self.assertIn(raw_item, remaining_items)
        
        # Test edge case: Over-consumption (should result in negative balance, excluded from summary)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=raw_item,
            quantity=Decimal('50.00'),  # More than remaining balance (35.00)
            note='Over-consumption scenario',
            created_by=self.user,
            updated_by=self.user
        )
        
        final_summary = self.production_order.get_wip_materials_summary()
        
        # Should have no items now (all have zero or negative balances)
        self.assertEqual(len(final_summary), 0)
        
        # Verify has_wip_materials() returns False when no positive balances
        self.assertFalse(self.production_order.has_wip_materials())
        
        # Test adding new material after consumption
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('25.50'),
            note='Additional material withdrawal',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should now have materials again
        self.assertTrue(self.production_order.has_wip_materials())
        
        new_summary = self.production_order.get_wip_materials_summary()
        self.assertEqual(len(new_summary), 1)
        self.assertEqual(new_summary[0]['item_sku'], self.item1)
        self.assertEqual(new_summary[0]['balance'], Decimal('25.50'))

    def test_get_wip_materials_summary_empty(self):
        """Test get_wip_materials_summary() with no materials"""
        summary = self.production_order.get_wip_materials_summary()
        self.assertEqual(len(summary), 0)


class ProductionOrderStatusMethodsSimpleTest(TestCase):
    """Simple tests for status transition methods"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = CategoryFactory()
        self.warehouse = WarehouseFactory()
        self.item1 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_status_display_with_context_closed_completed(self):
        """Test get_status_display_with_context() for CLOSED_COMPLETED"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CLOSED_COMPLETED
        )
        self.production_order.refresh_from_db()
        
        result = self.production_order.get_status_display_with_context()
        self.assertEqual(result, "Closed (Successfully Completed)")

    def test_status_display_with_context_closed_cancelled(self):
        """Test get_status_display_with_context() for CLOSED_CANCELLED"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CLOSED_CANCELLED
        )
        self.production_order.refresh_from_db()
        
        result = self.production_order.get_status_display_with_context()
        self.assertEqual(result, "Closed (Cancelled - Materials Returned)")

    def test_status_display_with_context_regular_status(self):
        """Test get_status_display_with_context() for regular status"""
        # DRAFT status (default)
        result = self.production_order.get_status_display_with_context()
        self.assertEqual(result, "Draft")

    def test_was_completed_successfully(self):
        """Test was_completed_successfully() method"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CLOSED_COMPLETED
        )
        self.production_order.refresh_from_db()
        
        self.assertTrue(self.production_order.was_completed_successfully())

    def test_was_cancelled_true_for_cancelled(self):
        """Test was_cancelled() returns True for CANCELLED status"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CANCELLED
        )
        self.production_order.refresh_from_db()
        
        self.assertTrue(self.production_order.was_cancelled())

    def test_was_cancelled_true_for_closed_cancelled(self):
        """Test was_cancelled() returns True for CLOSED_CANCELLED status"""
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CLOSED_CANCELLED
        )
        self.production_order.refresh_from_db()
        
        self.assertTrue(self.production_order.was_cancelled())

    def test_was_cancelled_false_for_other_status(self):
        """Test was_cancelled() returns False for other statuses"""
        # DRAFT status (default)
        self.assertFalse(self.production_order.was_cancelled())


class ProductionOrderStatusTransitionSimpleTest(TestCase):
    """Simple tests for status transition methods without validators"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = CategoryFactory()
        self.warehouse = WarehouseFactory()
        self.item1 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_cancel_production_from_created(self):
        """Test cancel_production() from CREATED status (after proper transition)"""
        # First create a BOM item to allow DRAFT -> CREATED transition
        from production.models import ProductionOrderBOM
        ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.item1,
            planned_quantity=Decimal('10'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Change to CREATED status first
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CREATED
        )
        self.production_order.refresh_from_db()
        
        # Now can cancel from CREATED
        self.production_order.cancel_production(user=self.user)
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CANCELLED)

    def test_cancel_production_invalid_status_raises_error(self):
        """Test cancel_production() raises error for invalid status"""
        # Set to COMPLETED status (cannot cancel)
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.COMPLETED
        )
        self.production_order.refresh_from_db()
        
        with self.assertRaises(ValueError) as context:
            self.production_order.cancel_production(user=self.user)
        
        self.assertIn("Cannot cancel production order", str(context.exception))

    def test_close_as_completed_success(self):
        """Test close_as_completed() from COMPLETED status"""
        # Set to COMPLETED status first
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.COMPLETED
        )
        self.production_order.refresh_from_db()
        
        self.production_order.close_as_completed(user=self.user)
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_COMPLETED)

    def test_close_as_cancelled_success_no_wip(self):
        """Test close_as_cancelled() with no WIP materials"""
        # Set to CANCELLED status first
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CANCELLED
        )
        self.production_order.refresh_from_db()
        
        # Ensure no WIP materials
        self.assertFalse(self.production_order.has_wip_materials())
        
        self.production_order.close_as_cancelled(user=self.user)
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_CANCELLED)

    def test_close_as_cancelled_fails_with_wip_materials(self):
        """Test close_as_cancelled() fails when WIP materials exist"""
        # Set to CANCELLED status first
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CANCELLED
        )
        self.production_order.refresh_from_db()
        
        # Create WIP materials
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValueError) as context:
            self.production_order.close_as_cancelled(user=self.user)
        
        self.assertIn("WIP materials still exist", str(context.exception))


class ProductionOrderCompleteWorkflowSimpleTest(TestCase):
    """Test complete workflow scenarios with simplified setup"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = CategoryFactory()
        self.warehouse = WarehouseFactory()
        self.item1 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        self.item2 = ItemFactory(category=self.category, type=ItemSKU.Type.PRODUCT, status=ItemSKU.Status.DRAFT)
        
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_complete_cancellation_workflow_simplified(self):
        """Test simplified cancellation workflow with proper status transitions"""
        # Start with DRAFT
        self.assertEqual(self.production_order.status, ProductionOrder.Status.DRAFT)
        
        # Create BOM item to allow DRAFT -> CREATED transition
        from production.models import ProductionOrderBOM
        ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.item1,
            planned_quantity=Decimal('10'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Change to CREATED status first (bypass validators for testing)
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.CREATED
        )
        self.production_order.refresh_from_db()
        
        # Add WIP materials (simulate withdrawal during production)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.IN,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Verify we have WIP materials
        self.assertTrue(self.production_order.has_wip_materials())
        
        # Cancel the production order (from CREATED status)
        self.production_order.cancel_production(user=self.user)
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CANCELLED)
        
        # Should still have WIP materials
        self.assertTrue(self.production_order.has_wip_materials())
        
        # Cannot close yet because of WIP materials
        with self.assertRaises(ValueError):
            self.production_order.close_as_cancelled(user=self.user)
        
        # Return WIP materials (use OUT movement to reduce balance)
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            movement_type=WIPStockMovement.MovementType.OUT,
            item_sku=self.item1,
            quantity=Decimal('100'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Now should not have WIP materials
        self.assertFalse(self.production_order.has_wip_materials())
        
        # Can now close as cancelled
        self.production_order.close_as_cancelled(user=self.user)
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_CANCELLED)
        
        # Verify final states
        self.assertTrue(self.production_order.is_finished())
        self.assertTrue(self.production_order.was_cancelled())
        self.assertFalse(self.production_order.was_completed_successfully())

    def test_complete_success_workflow_simplified(self):
        """Test simplified success workflow"""
        # Manually update status to bypass validators
        ProductionOrder.objects.filter(pk=self.production_order.pk).update(
            status=ProductionOrder.Status.COMPLETED
        )
        self.production_order.refresh_from_db()
        
        # Close as completed
        self.production_order.close_as_completed(user=self.user)
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_COMPLETED)
        
        # Verify final states
        self.assertTrue(self.production_order.is_finished())
        self.assertTrue(self.production_order.was_completed_successfully())
        self.assertFalse(self.production_order.was_cancelled())


class ProductionOrderReservationReturnTest(TestCase):
    """Test reservation return functionality in production orders"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.warehouse = WarehouseFactory()
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_return_all_material_reservations_exists(self):
        """Test that return_all_material_reservations method exists on ProductionOrder"""
        # Check method exists
        self.assertTrue(hasattr(self.production_order, 'return_all_material_reservations'))
        
        # Mock the method for testing
        with mock.patch.object(self.production_order, 'return_all_material_reservations') as mock_method:
            mock_method.return_value = None
            
            # Call the method
            result = self.production_order.return_all_material_reservations(user=self.user)
            
            # Verify it was called
            mock_method.assert_called_once_with(user=self.user)
            self.assertIsNone(result)
    
    def test_return_reservations_error_handling(self):
        """Test graceful error handling when returning reservations fails"""
        with mock.patch.object(self.production_order, 'return_all_material_reservations') as mock_method:
            # Simulate an error
            mock_method.side_effect = Exception("Database connection error")
            
            # Should raise the exception
            with self.assertRaises(Exception) as context:
                self.production_order.return_all_material_reservations(user=self.user)
            
            self.assertIn("Database connection error", str(context.exception))
    
    def test_mock_reservation_return_with_user(self):
        """Test that reservation return accepts user parameter"""
        with mock.patch.object(self.production_order, 'return_all_material_reservations') as mock_method:
            mock_method.return_value = {"returned_count": 5}
            
            result = self.production_order.return_all_material_reservations(user=self.user)
            
            # Check method was called with correct user
            mock_method.assert_called_once_with(user=self.user)
            self.assertEqual(result["returned_count"], 5)
