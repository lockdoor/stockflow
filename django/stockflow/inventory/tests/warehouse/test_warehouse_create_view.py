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
        """Test that warehouse creation creates warehouse-specific permissions and groups via transaction"""
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
        
        # Check main warehouse management permission was created
        main_perm_codename = f'can_manage_warehouse_{warehouse.id}'
        main_permission = Permission.objects.filter(codename=main_perm_codename).first()
        
        self.assertIsNotNone(main_permission, f"Main permission with codename '{main_perm_codename}' should exist")
        self.assertEqual(main_permission.name, f"Can manage Warehouse {warehouse.name} (ID {warehouse.id})")
        
        # Check that warehouse-specific group was created
        group_name = f"warehouse_{warehouse.id}_staff"
        warehouse_group = Group.objects.filter(name=group_name).first()
        self.assertIsNotNone(warehouse_group, f"Warehouse group '{group_name}' should exist")
        
        # Check that the group has the main permission
        self.assertIn(main_permission, warehouse_group.permissions.all())
        
        # Check that all warehouse-specific permissions were created (8 total)
        warehouse_permissions = Permission.objects.filter(
            codename__contains=f'_warehouse_{warehouse.id}'
        )
        expected_permission_count = 8  # As defined in _create_warehouse_permissions
        self.assertEqual(
            warehouse_permissions.count(), 
            expected_permission_count,
            f"Should create {expected_permission_count} warehouse-specific permissions"
        )
        
        # Verify the specific permissions exist
        expected_codenames = [
            f"can_manage_warehouse_{warehouse.id}",
            f"can_view_stock_warehouse_{warehouse.id}",
            f"can_create_stock_movement_warehouse_{warehouse.id}",
            f"can_manage_stock_movement_warehouse_{warehouse.id}",
            f"can_manage_reservation_warehouse_{warehouse.id}",
            f"can_create_production_order_warehouse_{warehouse.id}",
            f"can_manage_production_order_warehouse_{warehouse.id}",
            f"can_manage_production_process_warehouse_{warehouse.id}",
        ]
        
        for codename in expected_codenames:
            permission = Permission.objects.filter(codename=codename).first()
            self.assertIsNotNone(permission, f"Permission '{codename}' should exist")
            self.assertIn(permission, warehouse_group.permissions.all(), 
                         f"Permission '{codename}' should be in warehouse group")
        
        # Check that superuser group also has all the permissions
        superuser_group = Group.objects.filter(name='superuser').first()
        if superuser_group:
            for codename in expected_codenames:
                permission = Permission.objects.get(codename=codename)
                self.assertIn(permission, superuser_group.permissions.all(),
                             f"Permission '{codename}' should be in superuser group")
        
        # Verify counts increased correctly
        self.assertEqual(Warehouse.objects.count(), warehouse_count_before + 1)
        # Should create warehouse group + superuser group (if new)
        self.assertGreaterEqual(Group.objects.count(), group_count_before + 1)
        self.assertEqual(Permission.objects.count(), permission_count_before + expected_permission_count)

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
        
        # All warehouse-specific permissions should exist (8 total)
        warehouse_permissions = Permission.objects.filter(
            codename__contains=f'_warehouse_{warehouse.id}'
        )
        self.assertEqual(warehouse_permissions.count(), 8, "Should create 8 warehouse-specific permissions")
        
        # Warehouse-specific group should exist
        group_exists = Group.objects.filter(
            name=f'warehouse_{warehouse.id}_staff'
        ).exists()
        self.assertTrue(group_exists, "Warehouse group should be created with warehouse")
        
        # Main management permission should exist
        main_permission_exists = Permission.objects.filter(
            codename=f'can_manage_warehouse_{warehouse.id}'
        ).exists()
        self.assertTrue(main_permission_exists, "Main management permission should be created with warehouse")
        
        # Counts should increase correctly
        self.assertEqual(Warehouse.objects.count(), warehouse_count_before + 1)
        self.assertGreaterEqual(Group.objects.count(), group_count_before + 1)
        self.assertEqual(Permission.objects.count(), permission_count_before + 8)

    def test_warehouse_creator_gets_permission_automatically(self):
        """Test that the user who creates a warehouse automatically gets permission to manage it"""
        self.client.login(username='permitted', password='testpass123')
        url = reverse('inventory:warehouse-form')
        data = {
            'name': 'Creator Permission Test Warehouse',
            'code': 'CREATOR01',
            'is_active': True
        }
        
        # Verify user doesn't have warehouse permission before creation
        warehouse_exists_before = Warehouse.objects.filter(name="Creator Permission Test Warehouse").exists()
        self.assertFalse(warehouse_exists_before, "Warehouse should not exist before creation")
        
        response = self.client.post(url, data, follow=True)
        
        # Should redirect on success
        self.assertRedirects(response, reverse('inventory:warehouse-list'))
        
        # Get the created warehouse
        warehouse = Warehouse.objects.get(name="Creator Permission Test Warehouse")
        
        # Check that user has been added to the warehouse group automatically
        warehouse_group = warehouse.get_warehouse_group()
        self.assertIn(self.user_with_perm, warehouse_group.user_set.all(),
                     "Warehouse creator should be automatically added to warehouse group")
        
        # Check that user now has warehouse management permission
        main_permission = Permission.objects.get(
            codename=f'can_manage_warehouse_{warehouse.id}'
        )
        
        # User should have the permission either directly or through group membership
        has_permission = (
            self.user_with_perm.has_perm(f'inventory.can_manage_warehouse_{warehouse.id}') or
            main_permission in self.user_with_perm.get_group_permissions() or
            main_permission in self.user_with_perm.user_permissions.all()
        )
        self.assertTrue(has_permission, 
                       "Warehouse creator should have permission to manage the warehouse they created")
