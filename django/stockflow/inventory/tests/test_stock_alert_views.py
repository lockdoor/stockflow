"""
Test cases for Stock Alert Views

Tests for stock alert views including CRUD operations, bulk actions, and AJAX functionality.

Author: StockFlow Team
Created: 2025
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.http import Http404
from django.core.exceptions import PermissionDenied

from catalog.models import ItemSKU, Category
from inventory.models import Warehouse, Stock
from inventory.models.stock_alert import StockAlert
from inventory.forms.stock_alert_form import StockAlertForm, StockAlertSearchForm, BulkStockAlertForm

User = get_user_model()


class StockAlertViewTestCase(TestCase):
    """Base test case for stock alert views with common setup"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Grant permissions to admin user
        content_type = ContentType.objects.get_for_model(StockAlert)
        permissions = Permission.objects.filter(content_type=content_type)
        self.admin_user.user_permissions.set(permissions)
        
        # Create test category
        self.category = Category(
            name='Test Category',
            note='Test category for stock alert tests',
            created_by=self.user,
            updated_by=self.user
        )
        self.category.save()
        
        # Create test items
        self.item1 = ItemSKU(
            sku_code='TEST-001',
            name='Test Item 1',
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        self.item1.save()
        
        self.item2 = ItemSKU(
            sku_code='TEST-002',
            name='Test Item 2',
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        self.item2.save()
        
        # Create test warehouses
        self.warehouse1 = Warehouse(
            name='Main Warehouse',
            code='MAIN',
            address='Building A',
            created_by=self.user,
            updated_by=self.user
        )
        self.warehouse1.save()
        
        self.warehouse2 = Warehouse(
            name='Secondary Warehouse',
            code='SEC',
            address='Building B',
            created_by=self.user,
            updated_by=self.user
        )
        self.warehouse2.save()
        
        # Create test stock records
        self.stock1 = Stock(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            available_quantity=Decimal('100.00'),
            created_by=self.user,
            updated_by=self.user
        )
        self.stock1.save()
        
        self.stock2 = Stock(
            item_sku=self.item2,
            warehouse=self.warehouse2,
            lot_number='LOT002',
            available_quantity=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        self.stock2.save()
        
        # Create test stock alerts
        self.alert1 = StockAlert(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            minimum_threshold=Decimal('20.00'),
            critical_threshold=Decimal('10.00'),
            is_enabled=True,
            note='Test alert 1',
            created_by=self.user,
            updated_by=self.user
        )
        self.alert1.save()
        
        self.alert2 = StockAlert(
            item_sku=self.item2,
            warehouse=self.warehouse2,
            minimum_threshold=Decimal('15.00'),
            critical_threshold=Decimal('5.00'),
            is_enabled=False,
            note='Test alert 2',
            created_by=self.user,
            updated_by=self.user
        )
        self.alert2.save()
        
        self.client = Client()


class StockAlertListViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertListView"""
    
    def test_list_view_requires_login(self):
        """Test that list view requires login"""
        response = self.client.get(reverse('inventory:stock-alert-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_list_view_loads_successfully(self):
        """Test that list view loads successfully for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Alerts')
        self.assertContains(response, self.alert1.item_sku.sku_code)
        self.assertContains(response, self.alert2.item_sku.sku_code)
    
    def test_list_view_context_data(self):
        """Test that list view includes required context data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-list'))
        
        self.assertIn('search_form', response.context)
        self.assertIn('total_alerts', response.context)
        self.assertIn('enabled_alerts', response.context)
        self.assertIn('disabled_alerts', response.context)
        
        self.assertEqual(response.context['total_alerts'], 2)
        self.assertEqual(response.context['enabled_alerts'], 1)
        self.assertEqual(response.context['disabled_alerts'], 1)
    
    def test_list_view_search_functionality(self):
        """Test search functionality in list view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Search by item SKU code
        response = self.client.get(reverse('inventory:stock-alert-list'), {'search': 'TEST-001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
        # Check that only one alert is returned in the queryset
        self.assertEqual(len(response.context['stock_alerts']), 1)
        self.assertEqual(response.context['stock_alerts'][0].item_sku.sku_code, 'TEST-001')
        
        # Search by warehouse name
        response = self.client.get(reverse('inventory:stock-alert-list'), {'search': 'Main'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Main Warehouse')
        self.assertEqual(len(response.context['stock_alerts']), 1)
    
    def test_list_view_filtering(self):
        """Test filtering functionality in list view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Filter by enabled status
        response = self.client.get(reverse('inventory:stock-alert-list'), {'is_enabled': 'true'})
        self.assertEqual(response.status_code, 200)
        # Check that only enabled alert is in the queryset
        self.assertEqual(len(response.context['stock_alerts']), 1)
        self.assertEqual(response.context['stock_alerts'][0].item_sku.sku_code, 'TEST-001')
        self.assertTrue(response.context['stock_alerts'][0].is_enabled)
        
        # Filter by disabled status
        response = self.client.get(reverse('inventory:stock-alert-list'), {'is_enabled': 'false'})
        self.assertEqual(response.status_code, 200)
        # Check that only disabled alert is in the queryset
        self.assertEqual(len(response.context['stock_alerts']), 1)
        self.assertEqual(response.context['stock_alerts'][0].item_sku.sku_code, 'TEST-002')
        self.assertFalse(response.context['stock_alerts'][0].is_enabled)
        
        # Filter by item
        response = self.client.get(reverse('inventory:stock-alert-list'), {'item_sku': self.item1.id})
        self.assertEqual(response.status_code, 200)
        # Check that only alert for item1 is in the queryset
        self.assertEqual(len(response.context['stock_alerts']), 1)
        self.assertEqual(response.context['stock_alerts'][0].item_sku.sku_code, 'TEST-001')


class StockAlertDetailViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertDetailView"""
    
    def test_detail_view_requires_login(self):
        """Test that detail view requires login"""
        response = self.client.get(reverse('inventory:stock-alert-detail', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_detail_view_loads_successfully(self):
        """Test that detail view loads successfully for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-detail', kwargs={'pk': self.alert1.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alert1.item_sku.sku_code)
        self.assertContains(response, self.alert1.warehouse.name)
        self.assertContains(response, str(self.alert1.minimum_threshold))
        self.assertContains(response, str(self.alert1.critical_threshold))
    
    def test_detail_view_nonexistent_alert(self):
        """Test detail view with nonexistent alert"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)


class StockAlertCreateViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertCreateView"""
    
    def test_create_view_requires_login(self):
        """Test that create view requires login"""
        response = self.client.get(reverse('inventory:stock-alert-create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_create_view_requires_permission(self):
        """Test that create view requires appropriate permission"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-create'))
        self.assertEqual(response.status_code, 403)
    
    def test_create_view_loads_successfully_with_permission(self):
        """Test that create view loads successfully with proper permissions"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('inventory:stock-alert-create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Stock Alert')
        self.assertIsInstance(response.context['form'], StockAlertForm)
    
    def test_create_view_with_pre_selected_item_and_warehouse(self):
        """Test create view with pre-selected item and warehouse from query params"""
        self.client.login(username='adminuser', password='adminpass123')
        url = f"{reverse('inventory:stock-alert-create')}?item={self.item1.id}&warehouse={self.warehouse1.id}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('preselected_item', response.context)
        self.assertIn('preselected_warehouse', response.context)
        self.assertEqual(response.context['preselected_item'], self.item1)
        self.assertEqual(response.context['preselected_warehouse'], self.warehouse1)
    
    def test_create_alert_success(self):
        """Test successful alert creation"""
        self.client.login(username='adminuser', password='adminpass123')
        
        # Create a new item and warehouse combination that doesn't have an alert yet
        new_item = ItemSKU(
            sku_code='NEW-001',
            name='New Item',
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        new_item.save()
        
        form_data = {
            'item_sku': new_item.id,
            'warehouse': self.warehouse1.id,
            'minimum_threshold': '25.00',
            'critical_threshold': '15.00',
            'is_enabled': True,
            'note': 'New test alert'
        }
        
        response = self.client.post(reverse('inventory:stock-alert-create'), data=form_data)
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check that alert was created
        alert = StockAlert.objects.get(item_sku=new_item, warehouse=self.warehouse1)
        self.assertEqual(alert.minimum_threshold, Decimal('25.00'))
        self.assertEqual(alert.critical_threshold, Decimal('15.00'))
        self.assertTrue(alert.is_enabled)
        self.assertEqual(alert.note, 'New test alert')
        self.assertEqual(alert.created_by, self.admin_user)
    
    def test_create_alert_duplicate_error(self):
        """Test error when creating duplicate alert"""
        self.client.login(username='adminuser', password='adminpass123')
        
        form_data = {
            'item_sku': self.item1.id,
            'warehouse': self.warehouse1.id,
            'minimum_threshold': '25.00',
            'critical_threshold': '15.00',
            'is_enabled': True,
            'note': 'Duplicate alert'
        }
        
        response = self.client.post(reverse('inventory:stock-alert-create'), data=form_data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('A stock alert for TEST-001 in Main Warehouse already exists.', str(form.errors))
    
    def test_create_alert_invalid_thresholds(self):
        """Test error when critical threshold is higher than minimum threshold"""
        self.client.login(username='adminuser', password='adminpass123')
        
        new_item = ItemSKU(
            sku_code='NEW-002',
            name='New Item 2',
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        new_item.save()
        
        form_data = {
            'item_sku': new_item.id,
            'warehouse': self.warehouse1.id,
            'minimum_threshold': '10.00',
            'critical_threshold': '20.00',  # Higher than minimum
            'is_enabled': True,
            'note': 'Invalid thresholds'
        }
        
        response = self.client.post(reverse('inventory:stock-alert-create'), data=form_data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('Critical threshold must be less than or equal to minimum threshold.', str(form.errors))


class StockAlertUpdateViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertUpdateView"""
    
    def test_update_view_requires_login(self):
        """Test that update view requires login"""
        response = self.client.get(reverse('inventory:stock-alert-edit', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_update_view_requires_permission(self):
        """Test that update view requires appropriate permission"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-edit', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_update_view_loads_successfully_with_permission(self):
        """Test that update view loads successfully with proper permissions"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('inventory:stock-alert-edit', kwargs={'pk': self.alert1.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Edit Stock Alert - {self.alert1.item_sku.sku_code}')
        self.assertIsInstance(response.context['form'], StockAlertForm)
        
        # Check that form is pre-populated
        form = response.context['form']
        self.assertEqual(form.instance, self.alert1)
    
    def test_update_alert_success(self):
        """Test successful alert update"""
        self.client.login(username='adminuser', password='adminpass123')
        
        form_data = {
            'item_sku': self.alert1.item_sku.id,
            'warehouse': self.alert1.warehouse.id,
            'minimum_threshold': '30.00',  # Changed from 20.00
            'critical_threshold': '12.00',  # Changed from 10.00
            'is_enabled': False,  # Changed from True
            'note': 'Updated test alert'  # Changed note
        }
        
        response = self.client.post(reverse('inventory:stock-alert-edit', kwargs={'pk': self.alert1.pk}), data=form_data)
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check that alert was updated
        self.alert1.refresh_from_db()
        self.assertEqual(self.alert1.minimum_threshold, Decimal('30.00'))
        self.assertEqual(self.alert1.critical_threshold, Decimal('12.00'))
        self.assertFalse(self.alert1.is_enabled)
        self.assertEqual(self.alert1.note, 'Updated test alert')
        self.assertEqual(self.alert1.updated_by, self.admin_user)


class StockAlertDeleteViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertDeleteView"""
    
    def test_delete_view_requires_login(self):
        """Test that delete view requires login"""
        response = self.client.get(reverse('inventory:stock-alert-delete', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_delete_view_requires_permission(self):
        """Test that delete view requires appropriate permission"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('inventory:stock-alert-delete', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_delete_view_loads_successfully_with_permission(self):
        """Test that delete view loads successfully with proper permissions"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('inventory:stock-alert-delete', kwargs={'pk': self.alert1.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alert1.item_sku.sku_code)
        self.assertContains(response, 'confirm')
    
    def test_delete_alert_success(self):
        """Test successful alert deletion"""
        self.client.login(username='adminuser', password='adminpass123')
        
        alert_id = self.alert1.pk
        response = self.client.post(reverse('inventory:stock-alert-delete', kwargs={'pk': alert_id}))
        
        # Should redirect to list page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('inventory:stock-alert-list'))
        
        # Check that alert was deleted
        with self.assertRaises(StockAlert.DoesNotExist):
            StockAlert.objects.get(pk=alert_id)


class StockAlertBulkActionViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertBulkActionView"""
    
    def test_bulk_action_requires_login(self):
        """Test that bulk action requires login"""
        response = self.client.post(reverse('inventory:stock-alert-bulk-action'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_bulk_action_requires_permission(self):
        """Test that bulk action requires appropriate permission"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('inventory:stock-alert-bulk-action'))
        self.assertEqual(response.status_code, 403)
    
    def test_bulk_enable_alerts(self):
        """Test bulk enable action"""
        self.client.login(username='adminuser', password='adminpass123')
        
        # Create additional disabled alert
        alert3 = StockAlert(
            item_sku=self.item1,
            warehouse=self.warehouse2,
            minimum_threshold=Decimal('25.00'),
            critical_threshold=Decimal('15.00'),
            is_enabled=False,
            created_by=self.user,
            updated_by=self.user
        )
        alert3.save()
        
        form_data = {
            'action': 'enable',
            'selected_alerts': f'{self.alert2.id},{alert3.id}'
        }
        
        response = self.client.post(reverse('inventory:stock-alert-bulk-action'), data=form_data)
        
        # Should redirect to list page
        self.assertEqual(response.status_code, 302)
        
        # Check that alerts were enabled
        self.alert2.refresh_from_db()
        alert3.refresh_from_db()
        self.assertTrue(self.alert2.is_enabled)
        self.assertTrue(alert3.is_enabled)
    
    def test_bulk_disable_alerts(self):
        """Test bulk disable action"""
        self.client.login(username='adminuser', password='adminpass123')
        
        form_data = {
            'action': 'disable',
            'selected_alerts': f'{self.alert1.id}'
        }
        
        response = self.client.post(reverse('inventory:stock-alert-bulk-action'), data=form_data)
        
        # Should redirect to list page
        self.assertEqual(response.status_code, 302)
        
        # Check that alert was disabled
        self.alert1.refresh_from_db()
        self.assertFalse(self.alert1.is_enabled)
    
    def test_bulk_delete_alerts(self):
        """Test bulk delete action"""
        self.client.login(username='adminuser', password='adminpass123')
        
        alert_ids = [self.alert1.id, self.alert2.id]
        form_data = {
            'action': 'delete',
            'selected_alerts': ','.join(map(str, alert_ids))
        }
        
        response = self.client.post(reverse('inventory:stock-alert-bulk-action'), data=form_data)
        
        # Should redirect to list page
        self.assertEqual(response.status_code, 302)
        
        # Check that alerts were deleted
        remaining_alerts = StockAlert.objects.filter(id__in=alert_ids)
        self.assertEqual(remaining_alerts.count(), 0)
    
    def test_bulk_action_invalid_form(self):
        """Test bulk action with invalid form data"""
        self.client.login(username='adminuser', password='adminpass123')
        
        form_data = {
            'action': 'invalid_action',
            'selected_alerts': f'{self.alert1.id}'
        }
        
        response = self.client.post(reverse('inventory:stock-alert-bulk-action'), data=form_data)
        
        # Should redirect to list page with error message
        self.assertEqual(response.status_code, 302)


class StockAlertToggleViewTest(StockAlertViewTestCase):
    """Test cases for StockAlertToggleView (AJAX)"""
    
    def test_toggle_view_requires_login(self):
        """Test that toggle view requires login"""
        response = self.client.post(reverse('inventory:stock-alert-toggle', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_toggle_view_requires_permission(self):
        """Test that toggle view requires appropriate permission"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('inventory:stock-alert-toggle', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_toggle_alert_enable_to_disable(self):
        """Test toggling alert from enabled to disabled"""
        self.client.login(username='adminuser', password='adminpass123')
        
        # Alert 1 is currently enabled
        self.assertTrue(self.alert1.is_enabled)
        
        response = self.client.post(
            reverse('inventory:stock-alert-toggle', kwargs={'pk': self.alert1.pk}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertFalse(response_data['is_enabled'])
        
        # Check database
        self.alert1.refresh_from_db()
        self.assertFalse(self.alert1.is_enabled)
        self.assertEqual(self.alert1.updated_by, self.admin_user)
    
    def test_toggle_alert_disable_to_enable(self):
        """Test toggling alert from disabled to enabled"""
        self.client.login(username='adminuser', password='adminpass123')
        
        # Alert 2 is currently disabled
        self.assertFalse(self.alert2.is_enabled)
        
        response = self.client.post(
            reverse('inventory:stock-alert-toggle', kwargs={'pk': self.alert2.pk}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['is_enabled'])
        
        # Check database
        self.alert2.refresh_from_db()
        self.assertTrue(self.alert2.is_enabled)
        self.assertEqual(self.alert2.updated_by, self.admin_user)
    
    def test_toggle_nonexistent_alert(self):
        """Test toggling nonexistent alert"""
        self.client.login(username='adminuser', password='adminpass123')
        
        response = self.client.post(
            reverse('inventory:stock-alert-toggle', kwargs={'pk': 9999}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)


class StockAlertViewIntegrationTest(StockAlertViewTestCase):
    """Integration tests for stock alert views"""
    
    def test_create_edit_delete_workflow(self):
        """Test complete workflow: create → edit → delete"""
        self.client.login(username='adminuser', password='adminpass123')
        
        # Create new item for this test
        new_item = ItemSKU(
            sku_code='WORKFLOW-001',
            name='Workflow Test Item',
            category=self.category,
            unit='PCS',
            created_by=self.user,
            updated_by=self.user
        )
        new_item.save()
        
        # 1. Create alert
        create_data = {
            'item_sku': new_item.id,
            'warehouse': self.warehouse1.id,
            'minimum_threshold': '50.00',
            'critical_threshold': '20.00',
            'is_enabled': True,
            'note': 'Workflow test alert'
        }
        
        create_response = self.client.post(reverse('inventory:stock-alert-create'), data=create_data)
        self.assertEqual(create_response.status_code, 302)
        
        # Get created alert
        alert = StockAlert.objects.get(item_sku=new_item, warehouse=self.warehouse1)
        
        # 2. View detail
        detail_response = self.client.get(reverse('inventory:stock-alert-detail', kwargs={'pk': alert.pk}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'WORKFLOW-001')
        
        # 3. Edit alert
        edit_data = {
            'item_sku': new_item.id,
            'warehouse': self.warehouse1.id,
            'minimum_threshold': '60.00',  # Changed
            'critical_threshold': '25.00',  # Changed
            'is_enabled': False,  # Changed
            'note': 'Updated workflow test alert'  # Changed
        }
        
        edit_response = self.client.post(reverse('inventory:stock-alert-edit', kwargs={'pk': alert.pk}), data=edit_data)
        self.assertEqual(edit_response.status_code, 302)
        
        # Verify changes
        alert.refresh_from_db()
        self.assertEqual(alert.minimum_threshold, Decimal('60.00'))
        self.assertEqual(alert.critical_threshold, Decimal('25.00'))
        self.assertFalse(alert.is_enabled)
        
        # 4. Delete alert
        delete_response = self.client.post(reverse('inventory:stock-alert-delete', kwargs={'pk': alert.pk}))
        self.assertEqual(delete_response.status_code, 302)
        
        # Verify deletion
        with self.assertRaises(StockAlert.DoesNotExist):
            StockAlert.objects.get(pk=alert.pk)
    
    def test_list_view_pagination(self):
        """Test pagination in list view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create many alerts to test pagination
        for i in range(25):
            item = ItemSKU(
                sku_code=f'PAGE-{i:03d}',
                name=f'Page Test Item {i}',
                category=self.category,
                unit='PCS',
                created_by=self.user,
                updated_by=self.user
            )
            item.save()
            
            StockAlert(
                item_sku=item,
                warehouse=self.warehouse1,
                minimum_threshold=Decimal('10.00'),
                critical_threshold=Decimal('5.00'),
                is_enabled=True,
                created_by=self.user,
                updated_by=self.user
            ).save()
        
        # Test first page
        response = self.client.get(reverse('inventory:stock-alert-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['object_list']), 20)  # paginate_by = 20
        
        # Test second page
        response = self.client.get(reverse('inventory:stock-alert-list'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 7)  # 25 total - 20 first page + 2 original alerts
