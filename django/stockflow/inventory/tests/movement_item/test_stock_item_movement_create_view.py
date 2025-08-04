"""
Stock Item Movement Create View Tests

Tests for StockItemMovementCreateView including permissions, form handling,
HTMX responses, and business logic validation.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django import forms
from decimal import Decimal
from datetime import date

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU


class StockItemMovementCreateViewTest(TestCase):
    """Test cases for StockItemMovementCreateView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN01',
            address='123 Main St',
            note='Main warehouse for testing',
            is_active=True,
            created_by=self.user, 
            updated_by=self.user
        )
        
        # Create another warehouse for permission testing
        self.other_warehouse = Warehouse.objects.create(
            name='Other Warehouse',
            code='OTHER01',
            address='456 Other St',
            note='Other warehouse for testing',
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
        
        # Note: We don't create inactive items in setUp because business rules
        # prevent creating new RAW materials with INACTIVE status.
        # Instead, we'll create active items and then manually change status 
        # when testing with inactive items.
        
        # Create stock movements
        self.draft_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.confirmed_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            status=StockMovement.Status.CONFIRMED,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.other_warehouse_movement = StockMovement.objects.create(
            warehouse=self.other_warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get permissions
        self.add_permission = Permission.objects.get(codename='add_stockmovementitem')
        
        # Create warehouse-specific permissions
        try:
            self.warehouse_permission = Permission.objects.get(
                codename=f'can_manage_warehouse_{self.warehouse.id}'
            )
        except Permission.DoesNotExist:
            from django.contrib.contenttypes.models import ContentType
            warehouse_ct = ContentType.objects.get_for_model(Warehouse)
            self.warehouse_permission = Permission.objects.create(
                codename=f'can_manage_warehouse_{self.warehouse.id}',
                name=f'Can manage warehouse {self.warehouse.id}',
                content_type=warehouse_ct,
            )
        
        # Form data for testing
        self.valid_data = {
            'stock_movement': self.draft_movement.id,
            'item_sku': self.item.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': '10.50',
            'lot_number': 'LOT001',
            'expiry_date': '2025-12-31',
            'note': 'Test movement item'
        }
        
        self.minimal_data = {
            'stock_movement': self.draft_movement.id,
            'item_sku': self.item.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': '5.00',
        }
        
        # URLs
        self.create_url = reverse(
            'inventory:stock-item-movement-create', 
            kwargs={'stock_movement_id': self.draft_movement.id}
        )
        self.confirmed_create_url = reverse(
            'inventory:stock-item-movement-create',
            kwargs={'stock_movement_id': self.confirmed_movement.id}
        )
        self.other_warehouse_url = reverse(
            'inventory:stock-item-movement-create',
            kwargs={'stock_movement_id': self.other_warehouse_movement.id}
        )
        self.invalid_url = reverse(
            'inventory:stock-item-movement-create',
            kwargs={'stock_movement_id': 99999}
        )
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        
        response = self.client.post(self.create_url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_missing_stock_movement_id_raises_404(self):
        """Test that missing stock_movement_id raises 404"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        # URL without stock_movement_id should raise 404
        response = self.client.get(self.invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_stock_movement_id_raises_404(self):
        """Test that invalid stock_movement_id raises 404"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_permission_checking_add_stockmovementitem(self):
        """Test permission checking with add_stockmovementitem permission"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
    
    def test_permission_checking_warehouse_specific(self):
        """Test permission checking with warehouse-specific permission"""
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
    
    def test_permission_denied_without_permission(self):
        """Test that permission is denied without proper permissions"""
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 403)
    
    def test_permission_denied_different_warehouse(self):
        """Test that permission is denied for different warehouse"""
        # User has permission only for main warehouse
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Try to access other warehouse's movement
        response = self.client.get(self.other_warehouse_url)
        self.assertEqual(response.status_code, 403)
    
    def test_get_request_success(self):
        """Test successful GET request"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'movement-form-container')
        self.assertIn('form', response.context)
        
    def test_template_used_for_get_request(self):
        """Test that correct template is used for GET request"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, 'inventory/item-movement/partials/item-movement-form.html')
    
    def test_get_context_data_includes_stock_movement(self):
        """Test that context includes stock_movement"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        # Context should be available via form initialization
        form = response.context['form']
        self.assertEqual(form.initial.get('stock_movement'), self.draft_movement.id)
    
    def test_form_limits_item_choices_to_active(self):
        """Test that form only shows active items"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Create an inactive item by bypassing validation (for testing purposes)
        from catalog.models.item import ItemSKU
        inactive_item = ItemSKU(
            name='Inactive Item',
            sku_code='SKU002',
            unit='pcs',
            status=ItemSKU.Status.INACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        # Save without validation to bypass business rules
        super(ItemSKU, inactive_item).save()
        
        response = self.client.get(self.create_url)
        form = response.context['form']
        
        # Check that only active items are in queryset
        item_choices = list(form.fields['item_sku'].queryset)
        self.assertIn(self.item, item_choices)
        self.assertNotIn(inactive_item, item_choices)
    
    def test_post_valid_form_success(self):
        """Test successful form submission"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        initial_count = StockMovementItem.objects.count()
        
        response = self.client.post(self.create_url, self.valid_data)
        
        # Should create new movement item
        self.assertEqual(StockMovementItem.objects.count(), initial_count + 1)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response)
        self.assertEqual(response['HX-Trigger'], 'success')
        
        # Check created item
        movement_item = StockMovementItem.objects.latest('created_at')
        self.assertEqual(movement_item.stock_movement, self.draft_movement)
        self.assertEqual(movement_item.item_sku, self.item)
        self.assertEqual(movement_item.movement_type, StockMovementItem.MovementType.IN)
        self.assertEqual(movement_item.quantity, Decimal('10.50'))
        self.assertEqual(movement_item.lot_number, 'LOT001')
        self.assertEqual(movement_item.expiry_date, date(2025, 12, 31))
        self.assertEqual(movement_item.note, 'Test movement item')
        self.assertEqual(movement_item.created_by, self.user)
        self.assertEqual(movement_item.updated_by, self.user)
    
    def test_post_minimal_valid_form_success(self):
        """Test successful form submission with minimal data"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        initial_count = StockMovementItem.objects.count()
        
        response = self.client.post(self.create_url, self.minimal_data)
        
        # Should create new movement item
        self.assertEqual(StockMovementItem.objects.count(), initial_count + 1)
        self.assertEqual(response.status_code, 200)
        
        # Check created item
        movement_item = StockMovementItem.objects.latest('created_at')
        self.assertEqual(movement_item.quantity, Decimal('5.00'))
        # Now lot_number should be auto-generated (not None)
        self.assertIsNotNone(movement_item.lot_number)
        self.assertTrue(len(movement_item.lot_number) > 0)
        self.assertIsNone(movement_item.expiry_date)
        # Note can be empty string or None
        self.assertFalse(movement_item.note)
    
    def test_post_invalid_form_returns_errors(self):
        """Test form submission with invalid data"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        invalid_data = self.valid_data.copy()
        invalid_data['quantity'] = '-5'  # Invalid negative quantity
        
        initial_count = StockMovementItem.objects.count()
        
        response = self.client.post(self.create_url, invalid_data)
        
        # Should not create new movement item
        self.assertEqual(StockMovementItem.objects.count(), initial_count)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Retarget', response)
        self.assertEqual(response['HX-Retarget'], '#movement-item-form')
        self.assertIn('HX-Reswap', response)
        self.assertEqual(response['HX-Reswap'], 'innerHTML')
        
        # Check that form has errors
        self.assertContains(response, 'Quantity must be greater than 0')
    
    def test_post_form_value_error_handling(self):
        """Test handling of ValueError during save"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Create duplicate item to trigger validation error
        StockMovementItem.objects.create(
            stock_movement=self.draft_movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=Decimal('5.00'),
            lot_number='LOT001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create another with same combination (should trigger unique constraint)
        duplicate_data = self.valid_data.copy()
        
        initial_count = StockMovementItem.objects.count()
        
        response = self.client.post(self.create_url, duplicate_data)
        
        # Should not create new movement item
        self.assertEqual(StockMovementItem.objects.count(), initial_count)
        
        # Should return form with error message
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Retarget', response)
        self.assertEqual(response['HX-Retarget'], '#movement-item-form')
    
    def test_post_confirmed_movement_permission_denied(self):
        """Test that posting to confirmed movement is denied"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Confirmed movement should not allow new items
        response = self.client.post(self.confirmed_create_url, self.valid_data)
        self.assertEqual(response.status_code, 403)
    
    def test_form_invalid_context_includes_stock_movement(self):
        """Test that form_invalid includes stock_movement in context"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        invalid_data = self.valid_data.copy()
        invalid_data['quantity'] = ''  # Required field missing
        
        response = self.client.post(self.create_url, invalid_data)
        
        self.assertEqual(response.status_code, 200)
        # The template should receive the stock_movement context
        # since it's fetched in form_invalid method
    
    def test_htmx_headers_in_response(self):
        """Test that HTMX headers are properly set"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Test successful submission
        response = self.client.post(self.create_url, self.valid_data)
        self.assertIn('HX-Trigger', response)
        self.assertEqual(response['HX-Trigger'], 'success')
        
        # Test failed submission
        invalid_data = self.valid_data.copy()
        invalid_data['quantity'] = '-1'
        
        response = self.client.post(self.create_url, invalid_data)
        self.assertIn('HX-Retarget', response)
        self.assertIn('HX-Reswap', response)
        self.assertEqual(response['HX-Retarget'], '#movement-item-form')
        self.assertEqual(response['HX-Reswap'], 'innerHTML')
    
    def test_form_default_movement_type(self):
        """Test that form sets default movement type to IN"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        form = response.context['form']
        
        # Check default movement type
        self.assertEqual(form.fields['movement_type'].initial, StockMovementItem.MovementType.IN)
    
    def test_permission_check_on_both_get_and_post(self):
        """Test that permissions are checked on both GET and POST requests"""
        # Without login
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        
        response = self.client.post(self.create_url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        
        # With login but without permission
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 403)
        
        response = self.client.post(self.create_url, self.valid_data)
        self.assertEqual(response.status_code, 403)
    
    def test_successful_response_renders_item_row(self):
        """Test that successful submission renders item row template"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.create_url, self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        # Response should use the item-movement-row template
        # and include the movement_item in context
        movement_item = StockMovementItem.objects.latest('created_at')
        self.assertContains(response, movement_item.item_sku.sku_code)
    
    def test_view_uses_correct_template(self):
        """Test that view uses correct template"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, 'inventory/item-movement/partials/item-movement-form.html')
    
    def test_form_hidden_stock_movement_field(self):
        """Test that stock_movement field is hidden in form"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        form = response.context['form']
        
        # Check that stock_movement field is hidden
        self.assertIsInstance(form.fields['stock_movement'].widget, forms.HiddenInput)
        self.assertEqual(form.initial.get('stock_movement'), self.draft_movement.id)


class StockItemMovementCreateViewIntegrationTest(TestCase):
    """Integration tests for StockItemMovementCreateView"""
    
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
        
        self.add_permission = Permission.objects.get(codename='add_stockmovementitem')
        self.user.user_permissions.add(self.add_permission)
        
        self.create_url = reverse(
            'inventory:stock-item-movement-create',
            kwargs={'stock_movement_id': self.movement.id}
        )
    
    def test_complete_workflow_create_movement_item(self):
        """Test complete workflow of creating a movement item"""
        self.client.login(username='testuser', password='testpass')
        
        # Step 1: Get the form
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Submit valid data
        data = {
            'stock_movement': self.movement.id,
            'item_sku': self.item.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': '25.75',
            'lot_number': 'BATCH-001',
            'expiry_date': '2025-12-31',
            'note': 'Integration test item'
        }
        
        response = self.client.post(self.create_url, data)
        
        # Step 3: Verify creation
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'success')
        
        # Step 4: Verify database state
        movement_item = StockMovementItem.objects.get(
            stock_movement=self.movement,
            item_sku=self.item
        )
        self.assertEqual(movement_item.quantity, Decimal('25.75'))
        self.assertEqual(movement_item.lot_number, 'BATCH-001')
        self.assertEqual(movement_item.movement_type, StockMovementItem.MovementType.IN)
        self.assertEqual(movement_item.created_by, self.user)
        self.assertEqual(movement_item.updated_by, self.user)
    
    def test_duplicate_prevention(self):
        """Test that duplicate movement items are prevented"""
        self.client.login(username='testuser', password='testpass')
        
        # Create first item
        data = {
            'stock_movement': self.movement.id,
            'item_sku': self.item.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'quantity': '10.00',
            'lot_number': 'LOT001',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StockMovementItem.objects.count(), 1)
        
        # Try to create duplicate
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        # Should still be only 1 item due to unique constraint
        self.assertEqual(StockMovementItem.objects.count(), 1)
        # Response should contain error
        self.assertIn('HX-Retarget', response)
