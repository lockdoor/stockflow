"""
Stock Item Movement List View Tests

Tests for StockItemMovementListView including pagination, filtering,
and context data validation.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import Http404
from decimal import Decimal
from datetime import date

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU


class StockItemMovementListViewTest(TestCase):
    """Test cases for StockItemMovementListView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN01',
            address='123 Main St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create items
        self.item1 = ItemSKU.objects.create(
            name='Test Item 1',
            sku_code='SKU001',
            unit='pcs',
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            name='Test Item 2',
            sku_code='SKU002',
            unit='kg',
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movement
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create movement items
        self.movement_item1 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item1,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            expiry_date=date(2025, 12, 31),
            note='First test item',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.movement_item2 = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item2,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('5.50'),
            lot_number='LOT002',
            note='Second test item',
            created_by=self.user,
            updated_by=self.user
        )
        
        # URLs
        self.list_url = reverse(
            'inventory:stock-item-movement-list',
            kwargs={'stock_movement_id': self.movement.id}
        )
        self.invalid_url = reverse(
            'inventory:stock-item-movement-list',
            kwargs={'stock_movement_id': 99999}
        )
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_missing_stock_movement_id_raises_404(self):
        """Test that missing stock_movement_id raises 404"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_stock_movement_raises_404(self):
        """Test that invalid stock_movement raises 404"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_successful_get_request(self):
        """Test successful GET request"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/item-movement/partials/item-movement-list.html')
    
    def test_context_data_includes_stock_movement_id(self):
        """Test that context includes stock_movement"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stock_movement'], self.movement)
    
    def test_queryset_filters_by_stock_movement(self):
        """Test that queryset is filtered by stock_movement_id"""
        self.client.login(username='testuser', password='testpass')
        
        # Create new warehouse for another movement
        other_warehouse = Warehouse.objects.create(
            name='Secondary Warehouse',
            code='SEC01',
            address='456 Secondary St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another movement with items
        other_movement = StockMovement.objects.create(
            warehouse=other_warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        other_item = StockMovementItem.objects.create(
            stock_movement=other_movement,
            item_sku=self.item1,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('20.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Should only include items from the specified movement
        movement_items = response.context['movement_items']
        self.assertEqual(len(movement_items), 2)
        self.assertIn(self.movement_item1, movement_items)
        self.assertIn(self.movement_item2, movement_items)
        self.assertNotIn(other_item, movement_items)
    
    def test_queryset_ordering(self):
        """Test that queryset is ordered by -created_at"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        movement_items = list(response.context['movement_items'])
        
        # Items should be ordered by created_at descending
        # Since movement_item2 was created after movement_item1
        self.assertEqual(movement_items[0], self.movement_item2)
        self.assertEqual(movement_items[1], self.movement_item1)
    
    def test_pagination_settings(self):
        """Test pagination configuration"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Check paginate_by setting
        paginator = response.context['paginator']
        self.assertEqual(paginator.per_page, 20)
    
    def test_pagination_with_many_items(self):
        """Test pagination with more than 20 items"""
        self.client.login(username='testuser', password='testpass')
        
        # Create 25 additional movement items
        for i in range(25):
            StockMovementItem.objects.create(
                stock_movement=self.movement,
                item_sku=self.item1 if i % 2 == 0 else self.item2,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal(f'{i + 1}.00'),
                lot_number=f'LOT{i:03d}',
                created_by=self.user,
                updated_by=self.user
            )
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Should have pagination
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['movement_items']), 20)
        
        # Test page 2
        response = self.client.get(self.list_url + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movement_items']), 7)  # 27 total - 20 on page 1
    
    def test_context_object_name(self):
        """Test that context uses correct object name"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Should use 'movement_items' as context object name
        self.assertIn('movement_items', response.context)
    
    def test_empty_queryset(self):
        """Test view with no movement items"""
        self.client.login(username='testuser', password='testpass')
        
        # Delete all movement items
        StockMovementItem.objects.all().delete()
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        movement_items = response.context['movement_items']
        self.assertEqual(len(movement_items), 0)
    
    def test_view_with_nonexistent_movement_id_url_param(self):
        """Test view behavior with URL containing non-existent movement ID"""
        self.client.login(username='testuser', password='testpass')
        
        # Create URL with invalid stock_movement_id in kwargs
        invalid_url = reverse(
            'inventory:stock-item-movement-list',
            kwargs={'stock_movement_id': 99999}
        )
        
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_view_without_stock_movement_id_param(self):
        """Test view behavior when stock_movement_id is None"""
        self.client.login(username='testuser', password='testpass')
        
        # This would need a custom URL pattern or might not be possible
        # depending on your URL configuration
        # The view should raise Http404 when stock_movement_id is None
        pass
    
    def test_view_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/item-movement/partials/item-movement-list.html')
    
    def test_movement_items_display_data(self):
        """Test that movement items contain expected display data"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        movement_items = response.context['movement_items']
        self.assertEqual(len(movement_items), 2)
        
        # Convert to list for easier testing
        items_list = list(movement_items)
        
        # Find items by their IDs
        item1 = None
        item2 = None
        for item in items_list:
            if item.id == self.movement_item1.id:
                item1 = item
            elif item.id == self.movement_item2.id:
                item2 = item
        
        # Ensure both items were found
        self.assertIsNotNone(item1, "movement_item1 not found in response")
        self.assertIsNotNone(item2, "movement_item2 not found in response")
        
        # Check first item
        self.assertEqual(item1.item_sku.sku_code, 'SKU001')
        self.assertEqual(item1.movement_type, StockMovementItem.MovementType.IN)
        self.assertEqual(item1.quantity, Decimal('10.00'))
        self.assertEqual(item1.lot_number, 'LOT001')
        self.assertEqual(item1.note, 'First test item')
        
        # Check second item
        self.assertEqual(item2.item_sku.sku_code, 'SKU002')
        self.assertEqual(item2.movement_type, StockMovementItem.MovementType.OUT)
        self.assertEqual(item2.quantity, Decimal('5.50'))
        self.assertEqual(item2.lot_number, 'LOT002')
        self.assertEqual(item2.note, 'Second test item')


class StockItemMovementListViewIntegrationTest(TestCase):
    """Integration tests for StockItemMovementListView"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        self.warehouse = Warehouse.objects.create(
            name='Integration Test Warehouse',
            code='INT01',
            address='123 Integration St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            name='Integration Test Item',
            sku_code='INT-SKU001',
            unit='pcs',
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
        
        self.list_url = reverse(
            'inventory:stock-item-movement-list',
            kwargs={'stock_movement_id': self.movement.id}
        )
    
    def test_complete_workflow_list_movement_items(self):
        """Test complete workflow of listing movement items"""
        self.client.login(username='testuser', password='testpass')
        
        # Step 1: Initially empty list
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movement_items']), 0)
        
        # Step 2: Add some movement items
        for i in range(3):
            StockMovementItem.objects.create(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal(f'{(i+1)*10}.00'),
                lot_number=f'BATCH-{i+1:03d}',
                note=f'Integration test item {i+1}',
                created_by=self.user,
                updated_by=self.user
            )
        
        # Step 3: Verify updated list
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        movement_items = response.context['movement_items']
        self.assertEqual(len(movement_items), 3)
        
        # Verify ordering (latest first)
        quantities = [item.quantity for item in movement_items]
        self.assertEqual(quantities, [Decimal('30.00'), Decimal('20.00'), Decimal('10.00')])
    
    def test_cross_movement_isolation(self):
        """Test that movement items are properly isolated between movements"""
        self.client.login(username='testuser', password='testpass')
        
        # Create another warehouse for the second movement
        other_warehouse = Warehouse.objects.create(
            name='Secondary Warehouse',
            code='SEC01',
            address='456 Secondary St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another movement with different warehouse
        other_movement = StockMovement.objects.create(
            warehouse=other_warehouse,  # Different warehouse
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add items to first movement
        first_item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('100.00'),
            lot_number='BATCH-001',
            note='First movement item',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add items to second movement
        second_item = StockMovementItem.objects.create(
            stock_movement=other_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=Decimal('50.00'),
            lot_number='BATCH-002',
            note='Second movement item',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Verify first movement list (should only show items from self.movement)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        movement_items = response.context['movement_items']
        self.assertEqual(len(movement_items), 1)
        self.assertEqual(movement_items[0].id, first_item.id)
        self.assertEqual(movement_items[0].quantity, Decimal('100.00'))
        self.assertEqual(movement_items[0].movement_type, StockMovementItem.MovementType.IN)
        self.assertEqual(movement_items[0].stock_movement.warehouse.code, 'INT01')
        
        # Verify second movement list (should only show items from other_movement)
        other_list_url = reverse(
            'inventory:stock-item-movement-list',
            kwargs={'stock_movement_id': other_movement.id}
        )
        response = self.client.get(other_list_url)
        self.assertEqual(response.status_code, 200)
        movement_items = response.context['movement_items']
        self.assertEqual(len(movement_items), 1)
        self.assertEqual(movement_items[0].id, second_item.id)
        self.assertEqual(movement_items[0].quantity, Decimal('50.00'))
        self.assertEqual(movement_items[0].movement_type, StockMovementItem.MovementType.OUT)
        self.assertEqual(movement_items[0].stock_movement.warehouse.code, 'SEC01')
