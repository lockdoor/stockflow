"""
Test Warehouse Create View

Tests for warehouse creation view including permissions, form validation,
and HTMX integration with the refactored Warehouse model.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from inventory.models.warehouse import Warehouse


class WarehouseCreateViewTest(TestCase):
    """Test case for Warehouse create view"""

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
        
        # Add warehouse creation permission
        perm = Permission.objects.get(codename='add_warehouse')
        self.user_with_perm.user_permissions.add(perm)

    def test_redirect_if_not_logged_in(self):
        """Test redirect to login if user is not authenticated"""
        url = reverse('inventory:warehouse-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_forbidden_if_logged_in_without_permission(self):
        """Test 403 forbidden if user lacks add_warehouse permission"""
        self.client.login(username='tester', password='testpass123')
        url = reverse('inventory:warehouse-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_create_form_with_permission(self):
        """Test GET request returns form for user with permission"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertContains(response, 'Add New Warehouse')
        self.assertIn('form', response.context)

    def test_create_warehouse_success_with_all_fields(self):
        """Test successful warehouse creation with all fields"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Main Distribution Center',
            'code': 'MDC001',
            'address': '123 Industrial Blvd, Manufacturing District',
            'note': 'Primary distribution center for the region',
            'is_active': True,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Check warehouse was created
        warehouse = Warehouse.objects.get(name='Main Distribution Center')
        self.assertEqual(warehouse.code, 'MDC001')
        self.assertEqual(warehouse.address, '123 Industrial Blvd, Manufacturing District')
        self.assertTrue(warehouse.is_active)
        self.assertEqual(warehouse.created_by, self.user_with_perm)
        self.assertEqual(warehouse.updated_by, self.user_with_perm)
        
        # Check response contains warehouse row
        self.assertContains(response, 'warehouse-row')
        self.assertContains(response, 'MDC001')

    def test_create_warehouse_success_minimal_fields(self):
        """Test successful warehouse creation with minimal required fields"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Minimal Warehouse',
            'code': 'MIN001',
            'is_active': True,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Check warehouse was created
        warehouse = Warehouse.objects.get(name='Minimal Warehouse')
        self.assertEqual(warehouse.code, 'MIN001')
        self.assertTrue(warehouse.is_active)
        self.assertEqual(warehouse.address, '')
        self.assertEqual(warehouse.note, '')

    def test_create_warehouse_invalid_missing_name(self):
        """Test warehouse creation fails with missing name"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'code': 'NONAME01',
            'address': 'Address without name',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertFalse(Warehouse.objects.filter(code='NONAME01').exists())

    def test_create_warehouse_invalid_missing_code(self):
        """Test warehouse creation fails with missing code"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'No Code Warehouse',
            'address': 'Address without code',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        self.assertFalse(Warehouse.objects.filter(name='No Code Warehouse').exists())

    def test_create_warehouse_duplicate_code(self):
        """Test warehouse creation fails with duplicate code"""
        # Create existing warehouse
        existing = Warehouse(
            name='Existing Warehouse',
            code='DUP001',
            created_by=self.user_with_perm,
            updated_by=self.user_with_perm
        )
        # Use super save to bypass validation for test setup
        super(Warehouse, existing).save()
        
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Duplicate Code Warehouse',
            'code': 'DUP001',  # Same code
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-form')
        # Should only have the original warehouse
        self.assertEqual(Warehouse.objects.filter(code='DUP001').count(), 1)

    def test_create_warehouse_code_normalization(self):
        """Test that warehouse code is normalized to uppercase"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Lowercase Code Warehouse',
            'code': 'lower001',  # lowercase
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        
        # Check code was normalized
        warehouse = Warehouse.objects.get(name='Lowercase Code Warehouse')
        self.assertEqual(warehouse.code, 'LOWER001')

    def test_create_warehouse_non_htmx_request(self):
        """Test behavior for non-HTMX requests (should still work)"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Non HTMX Warehouse',
            'code': 'NHTMX01',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        # Should still create the warehouse
        self.assertTrue(Warehouse.objects.filter(name='Non HTMX Warehouse').exists())

    def test_create_warehouse_audit_fields(self):
        """Test that audit fields are properly set"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Audit Test Warehouse',
            'code': 'AUDIT01',
            'is_active': True
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        warehouse = Warehouse.objects.get(name='Audit Test Warehouse')
        self.assertEqual(warehouse.created_by, self.user_with_perm)
        self.assertEqual(warehouse.updated_by, self.user_with_perm)
        self.assertIsNotNone(warehouse.created_at)
        self.assertIsNotNone(warehouse.updated_at)
        self.assertEqual(warehouse.version, 1)
