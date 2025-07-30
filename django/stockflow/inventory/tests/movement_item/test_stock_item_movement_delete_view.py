"""
Stock Item Movement Delete View Tests

Tests for StockItemMovementDeleteView including permission checks,
status validation, and error handling.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from decimal import Decimal
from datetime import date

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU


class StockItemMovementDeleteViewTest(TestCase):
    """Test cases for StockItemMovementDeleteView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create item
        self.item = ItemSKU.objects.create(
            name='Test Item',
            sku_code='SKU001',
            unit='pcs',
            status=ItemSKU.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create draft stock movement
        self.draft_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create confirmed stock movement
        self.confirmed_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.CONFIRMED,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create movement items
        self.draft_item = StockMovementItem.objects.create(
            stock_movement=self.draft_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            note='Test item for deletion',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.confirmed_item = StockMovementItem.objects.create(
            stock_movement=self.confirmed_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('20.00'),
            lot_number='LOT002',
            note='Confirmed item',
            created_by=self.user,
            updated_by=self.user
        )
        
        # URLs
        self.delete_draft_url = reverse(
            'inventory:stock-item-movement-delete',
            kwargs={
                'stock_movement_id': self.draft_movement.id,
                'pk': self.draft_item.pk
            }
        )
        self.delete_confirmed_url = reverse(
            'inventory:stock-item-movement-delete',
            kwargs={
                'stock_movement_id': self.confirmed_movement.id,
                'pk': self.confirmed_item.pk
            }
        )
        
        # Add permissions
        self.delete_permission = Permission.objects.get(codename='delete_stockmovementitem')
        self.user.user_permissions.add(self.delete_permission)
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.delete(self.delete_draft_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_successful_delete_draft_item(self):
        """Test successful deletion of draft movement item"""
        self.client.login(username='testuser', password='testpass')
        
        # Verify item exists
        self.assertTrue(StockMovementItem.objects.filter(pk=self.draft_item.pk).exists())
        
        response = self.client.delete(self.delete_draft_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        self.assertEqual(response.headers['HX-Trigger'], 'success')
        
        # Verify item is deleted
        self.assertFalse(StockMovementItem.objects.filter(pk=self.draft_item.pk).exists())
    
    def test_delete_confirmed_movement_item_fails(self):
        """Test that deleting confirmed movement item fails"""
        self.client.login(username='testuser', password='testpass')
        
        # Verify item exists
        self.assertTrue(StockMovementItem.objects.filter(pk=self.confirmed_item.pk).exists())
        
        response = self.client.delete(self.delete_confirmed_url)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Cannot manage items in confirmed stock movements.", response.content.decode())
        
        # Verify item still exists
        self.assertTrue(StockMovementItem.objects.filter(pk=self.confirmed_item.pk).exists())
    
    def test_delete_nonexistent_item_returns_404(self):
        """Test deleting non-existent item returns 404"""
        self.client.login(username='testuser', password='testpass')
        
        nonexistent_url = reverse(
            'inventory:stock-item-movement-delete',
            kwargs={
                'stock_movement_id': self.draft_movement.id,
                'pk': 99999
            }
        )
        
        response = self.client.delete(nonexistent_url)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_without_permission_fails(self):
        """Test that delete without permission fails"""
        # Create user without permissions
        no_perm_user = User.objects.create_user(username='noperm', password='testpass')
        self.client.login(username='noperm', password='testpass')
        
        response = self.client.delete(self.delete_draft_url)
        self.assertEqual(response.status_code, 403)
    
    def test_delete_with_get_method_not_allowed(self):
        """Test that GET method is not allowed"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.delete_draft_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_delete_with_post_method_not_allowed(self):
        """Test that POST method is not allowed"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.delete_draft_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_htmx_response_headers(self):
        """Test HTMX response headers on successful delete"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(self.delete_draft_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        self.assertEqual(response.headers['HX-Trigger'], 'success')
        
        # Response should have no content
        self.assertEqual(len(response.content), 0)
    
    def test_warehouse_permission_check(self):
        """Test warehouse permission checking"""
        # Create another warehouse and user without access
        other_warehouse = Warehouse.objects.create(
            name='Other Warehouse',
            code='OTHER01',
            address='456 Other St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        other_movement = StockMovement.objects.create(
            warehouse=other_warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        other_item = StockMovementItem.objects.create(
            stock_movement=other_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create user with add permission but no warehouse access
        limited_user = User.objects.create_user(username='limited', password='testpass')
        add_permission = Permission.objects.get(codename='add_stockmovementitem')
        limited_user.user_permissions.add(add_permission)
        
        self.client.login(username='limited', password='testpass')
        
        delete_url = reverse(
            'inventory:stock-item-movement-delete',
            kwargs={
                'stock_movement_id': other_movement.id,
                'pk': other_item.pk
            }
        )
        
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 403)


class StockItemMovementDeleteViewIntegrationTest(TestCase):
    """Integration tests for StockItemMovementDeleteView"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Add permissions
        delete_permission = Permission.objects.get(codename='delete_stockmovementitem')
        self.user.user_permissions.add(delete_permission)
        
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
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_complete_workflow_delete_movement_item(self):
        """Test complete workflow of deleting movement items"""
        self.client.login(username='testuser', password='testpass')
        
        # Step 1: Create some movement items
        items = []
        for i in range(3):
            item = StockMovementItem.objects.create(
                stock_movement=self.movement,
                item_sku=self.item,
                movement_type=StockMovementItem.MovementType.IN,
                quantity=Decimal(f'{(i+1)*10}.00'),
                lot_number=f'BATCH-{i+1:03d}',
                note=f'Integration test item {i+1}',
                created_by=self.user,
                updated_by=self.user
            )
            items.append(item)
        
        # Verify all items exist
        self.assertEqual(StockMovementItem.objects.filter(stock_movement=self.movement).count(), 3)
        
        # Step 2: Delete items one by one
        for i, item in enumerate(items):
            delete_url = reverse(
                'inventory:stock-item-movement-delete',
                kwargs={
                    'stock_movement_id': self.movement.id,
                    'pk': item.pk
                }
            )
            
            response = self.client.delete(delete_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('HX-Trigger'), 'success')
            
            # Verify item is deleted
            self.assertFalse(StockMovementItem.objects.filter(pk=item.pk).exists())
            
            # Verify remaining items count
            remaining_count = 3 - (i + 1)
            self.assertEqual(
                StockMovementItem.objects.filter(stock_movement=self.movement).count(),
                remaining_count
            )
        
        # Step 3: Verify all items are deleted
        self.assertEqual(StockMovementItem.objects.filter(stock_movement=self.movement).count(), 0)
    
    def test_delete_from_different_movement_statuses(self):
        """Test deleting items from movements with different statuses"""
        self.client.login(username='testuser', password='testpass')
        
        # Create warehouse first
        another_warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create movements with different statuses
        draft_movement = StockMovement.objects.create(
            warehouse=another_warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        confirmed_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            status=StockMovement.Status.CONFIRMED,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create items in each movement
        draft_item = StockMovementItem.objects.create(
            stock_movement=draft_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        confirmed_item = StockMovementItem.objects.create(
            stock_movement=confirmed_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('20.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test deleting from draft (should succeed)
        draft_delete_url = reverse(
            'inventory:stock-item-movement-delete',
            kwargs={
                'stock_movement_id': draft_movement.id,
                'pk': draft_item.pk
            }
        )
        response = self.client.delete(draft_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StockMovementItem.objects.filter(pk=draft_item.pk).exists())
        
        # Test deleting from confirmed (should fail)
        confirmed_delete_url = reverse(
            'inventory:stock-item-movement-delete',
            kwargs={
                'stock_movement_id': confirmed_movement.id,
                'pk': confirmed_item.pk
            }
        )
        response = self.client.delete(confirmed_delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(StockMovementItem.objects.filter(pk=confirmed_item.pk).exists())
