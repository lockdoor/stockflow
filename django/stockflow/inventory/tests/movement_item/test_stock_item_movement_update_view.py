"""
Stock Item Movement Update View Tests

Tests for StockItemMovementUpdateView including form validation,
permission checks, status validation, and HTMX integration.

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


class StockItemMovementUpdateViewTest(TestCase):
    """Test cases for StockItemMovementUpdateView"""
    
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
            item_sku=self.item1,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('10.00'),
            lot_number='LOT001',
            note='Test item for update',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.confirmed_item = StockMovementItem.objects.create(
            stock_movement=self.confirmed_movement,
            item_sku=self.item2,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('20.00'),
            lot_number='LOT002',
            note='Confirmed item',
            created_by=self.user,
            updated_by=self.user
        )
        
        # URLs
        self.update_draft_url = reverse(
            'inventory:stock-item-movement-edit',
            kwargs={
                'stock_movement_id': self.draft_movement.id,
                'pk': self.draft_item.pk
            }
        )
        self.update_confirmed_url = reverse(
            'inventory:stock-item-movement-edit',
            kwargs={
                'stock_movement_id': self.confirmed_movement.id,
                'pk': self.confirmed_item.pk
            }
        )
        
        # Add permissions
        self.change_permission = Permission.objects.get(codename='change_stockmovementitem')
        self.user.user_permissions.add(self.change_permission)
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.update_draft_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_successful_get_draft_item_form(self):
        """Test successful GET request for draft movement item form"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.update_draft_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/item-movement/partials/item-movement-form.html')
        
        # Check form is pre-populated
        form = response.context['form']
        self.assertEqual(form.instance.item_sku, self.item1)
        self.assertEqual(form.instance.quantity, Decimal('10.00'))
        self.assertEqual(form.instance.lot_number, 'LOT001')
        self.assertEqual(form.instance.note, 'Test item for update')
    
    def test_get_confirmed_movement_item_fails(self):
        """Test that getting confirmed movement item form fails"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.update_confirmed_url)
        self.assertEqual(response.status_code, 403)
    
    def test_successful_post_update_draft_item(self):
        """Test successful POST request to update draft movement item"""
        self.client.login(username='testuser', password='testpass')
        
        update_data = {
            'stock_movement': self.draft_movement.id,
            'item_sku': self.item2.id,
            'movement_type': StockMovementItem.MovementType.OUT,
            'quantity': Decimal('15.50'),
            'lot_number': 'LOT001-UPDATED',
            'note': 'Updated test item'
        }
        
        response = self.client.post(self.update_draft_url, data=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        self.assertEqual(response.headers['HX-Trigger'], 'success')
        
        # Verify item is updated
        updated_item = StockMovementItem.objects.get(pk=self.draft_item.pk)
        self.assertEqual(updated_item.item_sku, self.item2)
        self.assertEqual(updated_item.movement_type, StockMovementItem.MovementType.OUT)
        self.assertEqual(updated_item.quantity, Decimal('15.50'))
        self.assertEqual(updated_item.lot_number, 'LOT001-UPDATED')
        self.assertEqual(updated_item.note, 'Updated test item')
        self.assertEqual(updated_item.updated_by, self.user)
    
    def test_post_confirmed_movement_item_fails(self):
        """Test that updating confirmed movement item fails"""
        self.client.login(username='testuser', password='testpass')
        
        update_data = {
            'item_sku': self.item1.id,
            'movement_type': StockMovementItem.MovementType.OUT,
            'quantity': Decimal('25.00'),
            'lot_number': 'LOT002-UPDATED',
            'note': 'Trying to update confirmed item'
        }
        
        response = self.client.post(self.update_confirmed_url, data=update_data)
        self.assertEqual(response.status_code, 403)
        
        # Verify item is not updated
        unchanged_item = StockMovementItem.objects.get(pk=self.confirmed_item.pk)
        self.assertEqual(unchanged_item.item_sku, self.item2)
        self.assertEqual(unchanged_item.quantity, Decimal('20.00'))
        self.assertEqual(unchanged_item.lot_number, 'LOT002')
        self.assertEqual(unchanged_item.note, 'Confirmed item')
    
    def test_update_nonexistent_item_returns_404(self):
        """Test updating non-existent item returns 404"""
        self.client.login(username='testuser', password='testpass')
        
        nonexistent_url = reverse(
            'inventory:stock-item-movement-edit',
            kwargs={
                'stock_movement_id': self.draft_movement.id,
                'pk': 99999
            }
        )
        
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)
    
    def test_update_without_permission_fails(self):
        """Test that update without permission fails"""
        # Create user without permissions
        no_perm_user = User.objects.create_user(username='noperm', password='testpass')
        self.client.login(username='noperm', password='testpass')
        
        response = self.client.get(self.update_draft_url)
        self.assertEqual(response.status_code, 403)
    
    def test_form_validation_errors(self):
        """Test form validation with invalid data"""
        self.client.login(username='testuser', password='testpass')
        
        invalid_data = {
            'item_sku': '',  # Required field
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': '-5.00',  # Invalid negative quantity
            'lot_number': 'TEST'
        }
        
        response = self.client.post(self.update_draft_url, data=invalid_data)
        self.assertEqual(response.status_code, 200)  # Form invalid, returns form with errors
        self.assertIn('HX-Retarget', response.headers)
        self.assertEqual(response.headers['HX-Retarget'], '#movement-item-form')
        
        # Check that form has errors
        form = response.context['form']
        self.assertTrue(form.errors)
    
    def test_context_data_includes_stock_movement(self):
        """Test that context includes stock movement and warehouse"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.update_draft_url)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.context['stock_movement'], self.draft_movement)
        self.assertEqual(response.context['warehouse'], self.warehouse)
    
    def test_update_with_get_method_allowed(self):
        """Test that GET method is allowed"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.update_draft_url)
        self.assertEqual(response.status_code, 200)
    
    def test_update_with_post_method_allowed(self):
        """Test that POST method is allowed"""
        self.client.login(username='testuser', password='testpass')
        
        update_data = {
            'item_sku': self.item1.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': Decimal('12.00'),
            'lot_number': 'LOT001'
        }
        
        response = self.client.post(self.update_draft_url, data=update_data)
        self.assertEqual(response.status_code, 200)
    
    def test_update_with_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(self.update_draft_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_htmx_response_headers_on_success(self):
        """Test HTMX response headers on successful update"""
        self.client.login(username='testuser', password='testpass')
        
        update_data = {
            'stock_movement': self.draft_movement.id,
            'item_sku': self.item1.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': Decimal('8.00'),
            'lot_number': 'LOT001-NEW'
        }
        
        response = self.client.post(self.update_draft_url, data=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        self.assertEqual(response.headers['HX-Trigger'], 'success')
        
        # Should render item-movement-row.html template
        self.assertTemplateUsed(response, 'inventory/item-movement/partials/item-movement-row.html')


class StockItemMovementUpdateViewIntegrationTest(TestCase):
    """Integration tests for StockItemMovementUpdateView"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Add permissions
        change_permission = Permission.objects.get(codename='change_stockmovementitem')
        self.user.user_permissions.add(change_permission)
        
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
    
    def test_complete_workflow_update_movement_item(self):
        """Test complete workflow of updating movement items"""
        self.client.login(username='testuser', password='testpass')
        
        # Step 1: Create a movement item
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('100.00'),
            lot_number='BATCH-001',
            note='Original item',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Step 2: Get the update form
        update_url = reverse(
            'inventory:stock-item-movement-edit',
            kwargs={
                'stock_movement_id': self.movement.id,
                'pk': item.pk
            }
        )
        
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Submit updated data
        update_data = {
            'stock_movement': self.movement.id,
            'item_sku': self.item.id,
            'movement_type': StockMovementItem.MovementType.OUT,
            'quantity': Decimal('75.50'),
            'lot_number': 'BATCH-001-UPDATED',
            'note': 'Updated integration test item',
            'expiry_date': '2025-12-31'
        }
        
        response = self.client.post(update_url, data=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('HX-Trigger'), 'success')
        
        # Step 4: Verify the update
        updated_item = StockMovementItem.objects.get(pk=item.pk)
        self.assertEqual(updated_item.movement_type, StockMovementItem.MovementType.OUT)
        self.assertEqual(updated_item.quantity, Decimal('75.50'))
        self.assertEqual(updated_item.lot_number, 'BATCH-001-UPDATED')
        self.assertEqual(updated_item.note, 'Updated integration test item')
        self.assertEqual(updated_item.updated_by, self.user)
    
    def test_update_multiple_items_in_sequence(self):
        """Test updating multiple items in sequence"""
        self.client.login(username='testuser', password='testpass')
        
        # Create multiple items
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
        
        # Update each item
        for i, item in enumerate(items):
            update_url = reverse(
                'inventory:stock-item-movement-edit',
                kwargs={
                    'stock_movement_id': self.movement.id,
                    'pk': item.pk
                }
            )
            
            update_data = {
                'stock_movement': self.movement.id,
                'item_sku': self.item.id,
                'movement_type': StockMovementItem.MovementType.OUT,
                'quantity': Decimal(f'{(i+1)*5}.00'),  # Different quantities
                'lot_number': f'UPDATED-BATCH-{i+1:03d}',
                'note': f'Updated item {i+1}'
            }
            
            response = self.client.post(update_url, data=update_data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('HX-Trigger'), 'success')
            
            # Verify individual update
            updated_item = StockMovementItem.objects.get(pk=item.pk)
            self.assertEqual(updated_item.movement_type, StockMovementItem.MovementType.OUT)
            self.assertEqual(updated_item.quantity, Decimal(f'{(i+1)*5}.00'))
            self.assertEqual(updated_item.lot_number, f'UPDATED-BATCH-{i+1:03d}')
            self.assertEqual(updated_item.note, f'Updated item {i+1}')
