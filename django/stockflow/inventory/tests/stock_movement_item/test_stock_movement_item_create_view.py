"""
Tests for StockItemMovementCreateView with redirect flow pattern

Tests the redirect flow functionality, form validation, permissions,
and business logic for creating stock movement items.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.urls import reverse
from django.http import Http404

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from inventory.views.stock_movement_item_views import StockItemMovementCreateView
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class StockItemMovementCreateViewTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        
        # Create warehouse - this will trigger permission creation
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create category for item
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create item SKU
        self.item_sku = ItemSKU.objects.create(
            sku_code='TEST001',
            name='Test Item',
            type=ItemSKU.Type.RAW,  # Use RAW type to avoid BOM validation
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movement
        self.stock_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=123,
            note='Test movement',
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get permissions
        stock_movement_item_content_type = ContentType.objects.get_for_model(StockMovementItem)
        self.base_permission = Permission.objects.get(
            codename='add_stockmovementitem',
            content_type=stock_movement_item_content_type
        )
        
        self.warehouse_permission = Permission.objects.get(
            codename=f'can_manage_warehouse_{self.warehouse.id}'
        )
        
        self.factory = RequestFactory()

    def test_get_request_with_permission(self):
        """Test GET request with proper permissions"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Item')
        self.assertContains(response, self.stock_movement.warehouse.name)
        self.assertIn('stock_movement', response.context)
        self.assertIn('warehouse', response.context)
        self.assertIn('movement_items', response.context)

    def test_get_request_without_permission(self):
        """Test GET request without permissions should be denied"""
        # Create a new user who doesn't have any permissions
        no_perm_user = User.objects.create_user(
            username='nopermuser',
            password='testpass123'
        )
        self.client.login(username='nopermuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)

    def test_get_request_with_warehouse_permission(self):
        """Test GET request with warehouse-specific permission"""
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_get_request_nonexistent_stock_movement(self):
        """Test GET request with non-existent stock movement should return 404"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_post_valid_form(self):
        """Test POST with valid form data"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,  # Add this hidden field
            'item_sku': self.item_sku.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',
            'quantity': 10,
            'note': 'Test note'
        }
        
        response = self.client.post(url, form_data)
        
        # Should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        
        # Check that item was created
        self.assertTrue(
            StockMovementItem.objects.filter(
                stock_movement=self.stock_movement,
                item_sku=self.item_sku,
                lot_number='LOT001',
                quantity=10
            ).exists()
        )
        
        # Check success message
        response = self.client.get(url)  # Follow redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Successfully added movement item' in str(m) for m in messages))

    def test_post_invalid_form(self):
        """Test POST with invalid form data"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,
            # 'item_sku': '',  # Completely omit required field
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',
            'quantity': 10
        }
        
        response = self.client.post(url, form_data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Please correct the errors below' in str(m) for m in messages))

    def test_post_negative_quantity(self):
        """Test POST with negative quantity should be invalid"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,
            'item_sku': self.item_sku.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',
            'quantity': -5  # Negative quantity
        }
        
        response = self.client.post(url, form_data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_post_zero_quantity(self):
        """Test POST with zero quantity should be invalid"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,
            'item_sku': self.item_sku.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',
            'quantity': 0  # Zero quantity
        }
        
        response = self.client.post(url, form_data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_post_duplicate_item_lot_combination(self):
        """Test POST with duplicate item-lot combination"""
        # First create a movement item
        StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            lot_number='LOT001',
            quantity=5,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,
            'item_sku': self.item_sku.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',  # Same lot number
            'quantity': 10
        }
        
        response = self.client.post(url, form_data)
        
        # Should handle duplicate validation
        self.assertEqual(response.status_code, 200)
        # The form should show validation error or handle it gracefully

    def test_post_confirmed_stock_movement(self):
        """Test POST to confirmed stock movement should be denied"""
        # Make stock movement confirmed
        self.stock_movement.status = StockMovement.Status.CONFIRMED
        self.stock_movement.save()
        
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,
            'item_sku': self.item_sku.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',
            'quantity': 10
        }
        
        response = self.client.post(url, form_data)
        
        # Should be denied based on business rules
        # This depends on how the form validates confirmed movements
        self.assertIn(response.status_code, [403, 200])  # Either forbidden or form error

    def test_context_data_includes_movement_items(self):
        """Test that context includes existing movement items"""
        # Create some existing movement items
        StockMovementItem.objects.create(
            stock_movement=self.stock_movement,
            item_sku=self.item_sku,
            movement_type=StockMovementItem.MovementType.IN,
            lot_number='LOT001',
            quantity=5,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('movement_items', response.context)
        self.assertEqual(len(response.context['movement_items']), 1)

    def test_form_kwargs_includes_stock_movement_id(self):
        """Test that form receives stock_movement_id in kwargs"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = StockItemMovementCreateView()
        view.request = request
        view.kwargs = {'stock_movement_id': self.stock_movement.id}
        
        form_kwargs = view.get_form_kwargs()
        
        self.assertIn('stock_movement_id', form_kwargs)
        self.assertEqual(form_kwargs['stock_movement_id'], self.stock_movement.id)

    def test_form_initial_includes_stock_movement(self):
        """Test that form initial data includes stock movement"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = StockItemMovementCreateView()
        view.request = request
        view.kwargs = {'stock_movement_id': self.stock_movement.id}
        
        initial = view.get_initial()
        
        self.assertIn('stock_movement', initial)
        self.assertEqual(initial['stock_movement'], self.stock_movement.id)

    def test_form_save_sets_created_updated_by(self):
        """Test that form save sets created_by and updated_by fields"""
        self.user.user_permissions.add(self.base_permission)
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:movement-create', kwargs={'stock_movement_id': self.stock_movement.id})
        form_data = {
            'stock_movement': self.stock_movement.id,
            'item_sku': self.item_sku.id,
            'movement_type': StockMovementItem.MovementType.IN,
            'lot_number': 'LOT001',
            'quantity': 10
        }
        
        self.client.post(url, form_data)
        
        movement_item = StockMovementItem.objects.get(
            stock_movement=self.stock_movement,
            lot_number='LOT001'
        )
        
        self.assertEqual(movement_item.created_by, self.user)
        self.assertEqual(movement_item.updated_by, self.user)

    def test_permission_required_base_is_set(self):
        """Test that permission_required_base is properly set"""
        view = StockItemMovementCreateView()
        self.assertEqual(view.permission_required_base, 'add_stockmovementitem')

    def test_template_name_is_set(self):
        """Test that template_name is properly set"""
        view = StockItemMovementCreateView()
        self.assertEqual(view.template_name, 'inventory/stock-movement-item/stock-movement-item-form.html')

    def test_model_is_set(self):
        """Test that model is properly set"""
        view = StockItemMovementCreateView()
        self.assertEqual(view.model, StockMovementItem)
