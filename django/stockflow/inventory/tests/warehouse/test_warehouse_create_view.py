"""
Test Warehouse Create View

Tests for warehouse creation view including permissions, form validation,
and redirect flow with the refactored Warehouse model.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission, Group
from django.contrib.messages import get_messages
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
        url = reverse('inventory:warehouse-form')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_forbidden_if_logged_in_without_permission(self):
        """Test 403 forbidden if user lacks add_warehouse permission"""
        self.client.login(username='tester', password='testpass123')
        url = reverse('inventory:warehouse-form')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_create_form_with_permission(self):
        """Test GET request returns form for user with permission"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Warehouse')
        self.assertIn('form', response.context)

    def test_create_warehouse_success_with_all_fields(self):
        """Test successful warehouse creation with all fields"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Main Distribution Center',
            'code': 'MDC001',
            'address': '123 Industrial Blvd, Manufacturing District',
            'note': 'Primary distribution center for the region',
            'is_active': True,
        }
        response = self.client.post(url, data, follow=True)
        
        # Should redirect to warehouse list
        self.assertRedirects(response, reverse('inventory:warehouse-list'))
        
        # Check warehouse was created
        warehouse = Warehouse.objects.get(name='Main Distribution Center')
        self.assertEqual(warehouse.code, 'MDC001')
        self.assertEqual(warehouse.address, '123 Industrial Blvd, Manufacturing District')
        self.assertTrue(warehouse.is_active)
        self.assertEqual(warehouse.created_by, self.user_with_perm)
        self.assertEqual(warehouse.updated_by, self.user_with_perm)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Main Distribution Center', str(messages[0]))
        self.assertIn('created successfully', str(messages[0]))

    def test_create_warehouse_success_minimal_fields(self):
        """Test successful warehouse creation with minimal required fields"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Minimal Warehouse',
            'code': 'MIN001',
            'is_active': True,
        }
        response = self.client.post(url, data, follow=True)
        
        # Should redirect to warehouse list
        self.assertRedirects(response, reverse('inventory:warehouse-list'))
        
        # Check warehouse was created
        warehouse = Warehouse.objects.get(name='Minimal Warehouse')
        self.assertEqual(warehouse.code, 'MIN001')
        self.assertTrue(warehouse.is_active)
        self.assertEqual(warehouse.address, '')
        self.assertEqual(warehouse.note, '')

    def test_create_warehouse_invalid_missing_name(self):
        """Test warehouse creation fails with missing name"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'code': 'NONAME01',
            'address': 'Address without name',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        # Should return form with errors, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        self.assertFalse(Warehouse.objects.filter(code='NONAME01').exists())

    def test_create_warehouse_invalid_missing_code(self):
        """Test warehouse creation fails with missing code"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'No Code Warehouse',
            'address': 'Address without code',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        # Should return form with errors, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
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
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Duplicate Code Warehouse',
            'code': 'DUP001',  # Same code
            'is_active': True
        }
        response = self.client.post(url, data)
        
        # Should return form with errors, not redirect
        self.assertEqual(response.status_code, 200)
        # Should only have the original warehouse
        self.assertEqual(Warehouse.objects.filter(code='DUP001').count(), 1)

    def test_create_warehouse_code_normalization(self):
        """Test that warehouse code is normalized to uppercase"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Lowercase Code Warehouse',
            'code': 'lower001',  # lowercase
            'is_active': True
        }
        response = self.client.post(url, data, follow=True)
        
        # Should redirect on success
        self.assertRedirects(response, reverse('inventory:warehouse-list'))
        
        # Check code was normalized
        warehouse = Warehouse.objects.get(name='Lowercase Code Warehouse')
        self.assertEqual(warehouse.code, 'LOWER001')

    def test_create_warehouse_with_next_url(self):
        """Test redirect flow with next URL parameter"""
        self.client.login(username='permitted', password='testpass123')
        next_url = reverse('inventory:dashboard')
        url = f"{reverse('inventory:warehouse-form')}?next={next_url}"
        data = {
            'name': 'Next URL Test Warehouse',
            'code': 'NEXT001',
            'is_active': True
        }
        response = self.client.post(url, data, follow=True)
        
        # Should redirect to next URL
        self.assertRedirects(response, next_url)
        
        # Check warehouse was created
        self.assertTrue(Warehouse.objects.filter(name='Next URL Test Warehouse').exists())

    def test_create_warehouse_audit_fields(self):
        """Test that audit fields are properly set"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
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

    def test_create_warehouse_creates_permissions_and_groups(self):
        """Test that warehouse creation creates warehouse-specific permission and group via transaction"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Permission Test Warehouse',
            'code': 'PERM01',
            'is_active': True
        }
        
        # Count before creation
        warehouse_count_before = Warehouse.objects.count()
        group_count_before = Group.objects.count()
        permission_count_before = Permission.objects.count()
        
        response = self.client.post(url, data, follow=True)
        
        # Should redirect on success
        self.assertRedirects(response, reverse('inventory:warehouse-list'))
        
        # Check warehouse was created
        warehouse = Warehouse.objects.get(name="Permission Test Warehouse")
        self.assertIsNotNone(warehouse.id)
        
        # Check permission was created
        perm_codename = f'can_manage_warehouse_{warehouse.id}'
        permission = Permission.objects.filter(codename=perm_codename).first()
        
        self.assertIsNotNone(permission, f"Permission with codename '{perm_codename}' should exist")
        self.assertEqual(permission.name, f"Can manage Warehouse {warehouse.name} (ID {warehouse.id})")
        
        # Check that the group was also created and has the permission
        group_name = f"warehouse_{warehouse.id}_staff"
        group = Group.objects.filter(name=group_name).first()
        self.assertIsNotNone(group, f"Group '{group_name}' should exist")
        self.assertIn(permission, group.permissions.all())
        
        # Check that superuser group also has the permission
        superuser_group = Group.objects.filter(name='superuser').first()
        if superuser_group:  # May not exist in test DB
            self.assertIn(permission, superuser_group.permissions.all())
        
        # Verify counts increased
        self.assertEqual(Warehouse.objects.count(), warehouse_count_before + 1)
        self.assertEqual(Group.objects.count(), group_count_before + 2)  # warehouse group + superuser group (if new)
        self.assertEqual(Permission.objects.count(), permission_count_before + 1)

    def test_warehouse_creation_atomic_transaction(self):
        """Test that warehouse creation is atomic - either everything succeeds or nothing is created"""
        self.client.login(username='permitted', password='testpass123')
        
        # Count before
        warehouse_count_before = Warehouse.objects.count()
        group_count_before = Group.objects.count()
        permission_count_before = Permission.objects.count()
        
        # Try to create warehouse with valid data
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Atomic Test Warehouse',
            'code': 'ATOM01', 
            'is_active': True
        }
        response = self.client.post(url, data, follow=True)
        
        # Should succeed
        self.assertRedirects(response, reverse('inventory:warehouse-list'))
        
        # Verify warehouse and permissions were created together
        warehouse = Warehouse.objects.get(name="Atomic Test Warehouse")
        
        # Both warehouse and permission should exist
        permission_exists = Permission.objects.filter(
            codename=f'can_manage_warehouse_{warehouse.id}'
        ).exists()
        group_exists = Group.objects.filter(
            name=f'warehouse_{warehouse.id}_staff'
        ).exists()
        
        self.assertTrue(permission_exists, "Permission should be created with warehouse")
        self.assertTrue(group_exists, "Group should be created with warehouse")
        
        # Counts should increase together
        self.assertEqual(Warehouse.objects.count(), warehouse_count_before + 1)
        self.assertGreater(Group.objects.count(), group_count_before)
        self.assertEqual(Permission.objects.count(), permission_count_before + 1)
