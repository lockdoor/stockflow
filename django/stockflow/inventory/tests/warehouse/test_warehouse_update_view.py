"""
Test Warehouse Update View

Tests for warehouse update view including permissions, form validation,
and HTMX integration with the refactored Warehouse model.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from inventory.models.warehouse import Warehouse


class WarehouseUpdateViewTest(TestCase):
    """Test case for Warehouse update view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='tester',
            password='testpass123'
        )
        self.user_with_perm = User.objects.create_user(
            username='permitted', 
            password='testpass123'
        )
        
        # Add warehouse change permission
        perm = Permission.objects.get(codename='change_warehouse')
        self.user_with_perm.user_permissions.add(perm)
        
        # Create test warehouse
        self.warehouse = Warehouse(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test Street',
            note='Original note',
            is_active=True,
            created_by=self.user_with_perm,
            updated_by=self.user_with_perm
        )
        super(Warehouse, self.warehouse).save()

    def test_redirect_if_not_logged_in(self):
        """Test redirect to login if user is not authenticated"""
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_forbidden_if_logged_in_without_permission(self):
        """Test 403 forbidden if user lacks change_warehouse permission"""
        self.client.login(username='tester', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_update_form_with_permission(self):
        """Test GET request returns form for user with permission"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertIn('form', response.context)
        
        # Check that form is pre-populated with warehouse data
        form = response.context['form']
        self.assertEqual(form.instance, self.warehouse)
        self.assertEqual(form.initial.get('name') or form.instance.name, 'Test Warehouse')
        self.assertEqual(form.initial.get('code') or form.instance.code, 'TEST01')

    def test_update_warehouse_success_with_all_fields(self):
        """Test successful warehouse update with all fields"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Updated Warehouse Name',
            'code': 'UPD001',
            'address': '456 Updated Street, New District',
            'note': 'Updated note with new information',
            'is_active': False,  # Change status
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh warehouse from database
        self.warehouse.refresh_from_db()
        
        # Check warehouse was updated
        self.assertEqual(self.warehouse.name, 'Updated Warehouse Name')
        self.assertEqual(self.warehouse.code, 'UPD001')
        self.assertEqual(self.warehouse.address, '456 Updated Street, New District')
        self.assertEqual(self.warehouse.note, 'Updated note with new information')
        self.assertFalse(self.warehouse.is_active)
        self.assertEqual(self.warehouse.updated_by, self.user_with_perm)
        
        # Check response contains updated warehouse row
        self.assertContains(response, 'warehouse-row')
        self.assertContains(response, 'UPD001')

    def test_update_warehouse_partial_fields(self):
        """Test successful warehouse update with partial fields"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Partially Updated Name',
            'code': 'PART01',
            'address': '123 Test Street',  # Keep original
            'note': '',  # Clear note
            'is_active': True,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh warehouse from database
        self.warehouse.refresh_from_db()
        
        # Check warehouse was updated
        self.assertEqual(self.warehouse.name, 'Partially Updated Name')
        self.assertEqual(self.warehouse.code, 'PART01')
        self.assertEqual(self.warehouse.address, '123 Test Street')
        self.assertEqual(self.warehouse.note, '')
        self.assertTrue(self.warehouse.is_active)

    def test_update_warehouse_invalid_missing_name(self):
        """Test warehouse update fails with missing name"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': '',  # Missing name
            'code': 'NONAME01',
            'address': 'Address without name',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertContains(response, 'This field is required.')  # Check for validation error
        
        # Check warehouse was not updated
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.name, 'Test Warehouse')  # Original name

    def test_update_warehouse_invalid_missing_code(self):
        """Test warehouse update fails with missing code"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Updated Name',
            'code': '',  # Missing code
            'address': 'Address without code',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertContains(response, 'This field is required.')  # Check for validation error
        
        # Check warehouse was not updated
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.code, 'TEST01')  # Original code

    def test_update_warehouse_duplicate_code(self):
        """Test warehouse update fails with duplicate code"""
        # Create another warehouse
        other_warehouse = Warehouse(
            name='Other Warehouse',
            code='OTHER01',
            created_by=self.user_with_perm,
            updated_by=self.user_with_perm
        )
        super(Warehouse, other_warehouse).save()
        
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Updated Name',
            'code': 'OTHER01',  # Duplicate code
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertContains(response, 'Warehouse with this Code already exists.')  # Check for validation error
        
        # Check warehouse was not updated
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.code, 'TEST01')  # Original code

    def test_update_warehouse_code_normalization(self):
        """Test that warehouse code is normalized to uppercase during update"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Updated Name',
            'code': 'lower001',  # lowercase
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Check code was normalized
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.code, 'LOWER001')

    def test_update_warehouse_non_htmx_request(self):
        """Test behavior for non-HTMX requests (should still work)"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Non HTMX Updated',
            'code': 'NHTMX01',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        # Should still update the warehouse
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.name, 'Non HTMX Updated')

    def test_update_warehouse_audit_fields(self):
        """Test that audit fields are properly updated"""
        original_created_at = self.warehouse.created_at
        original_created_by = self.warehouse.created_by
        original_version = self.warehouse.version
        
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Audit Test Update',
            'code': 'AUDIT01',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.warehouse.refresh_from_db()
        
        # Check audit fields
        self.assertEqual(self.warehouse.created_by, original_created_by)  # Should not change
        self.assertEqual(self.warehouse.created_at, original_created_at)  # Should not change
        self.assertEqual(self.warehouse.updated_by, self.user_with_perm)  # Should be updated
        self.assertGreater(self.warehouse.updated_at, original_created_at)  # Should be newer
        self.assertGreater(self.warehouse.version, original_version)  # Should increment

    def test_update_warehouse_404_for_nonexistent_warehouse(self):
        """Test that updating non-existent warehouse returns 404"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[99999])  # Non-existent ID
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_update_warehouse_same_code_allowed(self):
        """Test that updating warehouse with same code is allowed"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Updated Name Same Code',
            'code': 'TEST01',  # Same code as original
            'address': 'Updated address',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Check warehouse was updated
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.name, 'Updated Name Same Code')
        self.assertEqual(self.warehouse.code, 'TEST01')  # Code should remain same
        self.assertEqual(self.warehouse.address, 'Updated address')

    def test_update_warehouse_version_increment(self):
        """Test that version is incremented on update"""
        original_version = self.warehouse.version
        
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Version Test Update',
            'code': 'VER001',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.version, original_version + 1)

    def test_update_warehouse_status_change(self):
        """Test updating warehouse status from active to inactive and vice versa"""
        # Initially active
        self.assertTrue(self.warehouse.is_active)
        
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        
        # Update to inactive
        data = {
            'name': 'Status Test Warehouse',
            'code': 'STATUS01',
            'is_active': False
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.warehouse.refresh_from_db()
        self.assertFalse(self.warehouse.is_active)
        
        # Update back to active
        data['is_active'] = True
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.warehouse.refresh_from_db()
        self.assertTrue(self.warehouse.is_active)
