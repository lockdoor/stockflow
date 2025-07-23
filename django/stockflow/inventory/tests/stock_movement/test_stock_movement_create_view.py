"""
Stock Movement Create View Tests - Clean Version without Mocks

Tests for StockMovementCreateView including permissions, form handling,
HTMX responses, and business logic validation using real templates.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.core.exceptions import ValidationError

from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse


class StockMovementCreateViewTest(TestCase):
    """Test cases for StockMovementCreateView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN01',
            address='123 Main St',
            note='Main warehouse for testing',
            is_active=True,
            created_by=self.user, 
            updated_by=self.user
        )
        self.data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'note': 'Test stock movement',
            'warehouse': self.warehouse.id,
        }
        
        # Get permissions
        self.add_permission = Permission.objects.get(codename='add_stockmovement')
        try:
            self.warehouse_permission = Permission.objects.get(
                codename=f'can_manage_warehouse_{self.warehouse.id}'
            )
        except Permission.DoesNotExist:
            # Create the permission if it doesn't exist
            from django.contrib.contenttypes.models import ContentType
            warehouse_ct = ContentType.objects.get_for_model(Warehouse)
            self.warehouse_permission = Permission.objects.create(
                codename=f'can_manage_warehouse_{self.warehouse.id}',
                name=f'Can manage warehouse {self.warehouse.id}',
                content_type=warehouse_ct,
            )
        
        self.create_url = reverse('inventory:stock-movement-create', args=[self.warehouse.id])
        self.invalid_warehouse_url = reverse('inventory:stock-movement-create', args=[99999])
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        
        response = self.client.post(self.create_url, {})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_permission_checking_add_stockmovement(self):
        """Test permission checking with add_stockmovement permission"""
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
    
    def test_warehouse_specific_permission_restricted(self):
        """Test that only warehouse-specific permission allows access to specific warehouse"""
        other_warehouse = Warehouse.objects.create(
            name='Other Warehouse',
            code='OTHER01',
            address='Other Address',
            note='Another warehouse',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create URL for other warehouse
        other_create_url = reverse('inventory:stock-movement-create', kwargs={'warehouse_id': other_warehouse.pk})
        
        # Grant ONLY warehouse-specific permission for original warehouse (NO global permission)
        from django.contrib.contenttypes.models import ContentType
        warehouse_ct = ContentType.objects.get_for_model(Warehouse)
        warehouse_permission, _ = Permission.objects.get_or_create(
            codename=f'can_manage_warehouse_{self.warehouse.id}',
            name=f'Can manage warehouse {self.warehouse.id}',
            content_type=warehouse_ct,
        )
        
        # Give ONLY warehouse-specific permission, NOT global permission
        self.user.user_permissions.add(warehouse_permission)
        
        self.client.login(username='testuser', password='testpass')
        
        # Should have access to original warehouse via warehouse-specific permission
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        
        # Should NOT have access to other warehouse (GET request)
        response = self.client.get(other_create_url)
        self.assertEqual(response.status_code, 403)
        
        # Should NOT be able to create in other warehouse (POST request)
        initial_count = StockMovement.objects.count()
        other_data = self.data.copy()
        response = self.client.post(other_create_url, other_data)
        self.assertEqual(response.status_code, 403)
        
        # Verify no stock movement was created
        final_count = StockMovement.objects.count()
        self.assertEqual(initial_count, final_count, 
                        "Stock movement should not be created in unauthorized warehouse")
    
    def test_get_form_displays_correctly(self):
        """Test that GET request displays form correctly"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        
        # Check that warehouse is pre-selected
        form = response.context['form']
        self.assertEqual(form.initial.get('warehouse'), self.warehouse.id)

    def test_nonexistent_return_form_with_errors(self):
        """Test that non-existent warehouse returns form with errors"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.invalid_warehouse_url)
        self.assertEqual(response.status_code, 200)
        # context should contain form with errors
        self.assertIn('form', response.context)
    
    def test_successful_stock_movement_creation(self):
        """Test successful stock movement creation"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,
            'reference_id': 123,
            'note': 'Test stock movement',
            'warehouse': self.warehouse.id,
        }
        
        response = self.client.post(self.create_url, data)
        # Should be successful (200 for HTMX or 302 for redirect)
        self.assertIn(response.status_code, [200, 302])
        
        # Check that stock movement was created
        movement = StockMovement.objects.get(note='Test stock movement')
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.PACKING_LIST)
        self.assertEqual(movement.reference_id, 123)
        self.assertEqual(movement.warehouse, self.warehouse)
        self.assertEqual(movement.created_by, self.user)
        self.assertEqual(movement.updated_by, self.user)
        self.assertEqual(movement.status, StockMovement.Status.DRAFT)
    
    def test_creation_with_none_reference_type(self):
        """Test creation with NONE reference type"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': 'Movement with no reference',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertIn(response.status_code, [200, 302])
        
        movement = StockMovement.objects.get(note='Movement with no reference')
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.NONE)
        self.assertIsNone(movement.reference_id)
    
    def test_form_validation_errors(self):
        """Test form validation errors"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Missing required fields
        # data = {'warehouse': self.warehouse.id}
        data = {'note': 'Test stock movement'}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertContains(response, 'This field is required')
        
        # Missing reference_id for non-NONE type
        # data = {
        #     'reference_type': StockMovement.ReferenceType.INVOICE,
        #     'warehouse': self.warehouse.id,
        # }
        # response = self.client.post(self.create_url, data)
        # self.assertEqual(response.status_code, 200)
        # self.assertContains(response, 'Reference ID is required')
    
    def test_form_template_used(self):
        """Test that correct template is used"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, 'inventory/stock-movement/partials/stock-movement-form.html')
    
    def test_context_data(self):
        """Test that proper context data is provided"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        self.assertIn('form', response.context)
        self.assertIn('warehouse', response.context['form'].initial)


class StockMovementCreateViewBusinessLogicTest(TestCase):
    """Test business logic and edge cases for StockMovementCreateView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Business Test Warehouse',
            code='BIZTEST01',
            address='123 Business St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.add_permission = Permission.objects.get(codename='add_stockmovement')
        self.user.user_permissions.add(self.add_permission)
        self.create_url = reverse('inventory:stock-movement-create', args=[self.warehouse.id])
    
    def test_unique_draft_constraint_handling(self):
        """Test handling of unique draft constraint - only one draft per warehouse"""
        self.client.login(username='testuser', password='testpass')
        
        # Create first draft movement
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': 'First draft',
        }
        response = self.client.post(self.create_url, data)
        self.assertIn(response.status_code, [200, 302])
        
        # Verify first draft was created
        first_draft = StockMovement.objects.get(note='First draft')
        self.assertEqual(first_draft.status, StockMovement.Status.DRAFT)
        
        # Try to create second draft movement for same warehouse
        data['note'] = 'Second draft'
        response = self.client.post(self.create_url, data)
        
        # Should fail due to unique draft constraint
        self.assertEqual(response.status_code, 200)  # Form redisplayed with error
        self.assertContains(response, 'already has a draft stock movement')
        
        # Verify only one draft exists
        draft_count = StockMovement.objects.filter(
            warehouse=self.warehouse, 
            status=StockMovement.Status.DRAFT
        ).count()
        self.assertEqual(draft_count, 1)
    
    def test_reference_type_and_id_validation(self):
        """Test validation of reference_type and reference_id consistency"""
        self.client.login(username='testuser', password='testpass')
        
        # Test NONE type with reference_id (should be cleared by form)
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'reference_id': 123,  # This should be ignored/cleared
            'warehouse': self.warehouse.id,
            'note': 'None type with ID',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertIn(response.status_code, [200, 302])
        
        movement = StockMovement.objects.get(note='None type with ID')
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.NONE)
        self.assertIsNone(movement.reference_id)  # Should be cleared
        
        # Clean up for next test
        movement.delete()
        
        # Test non-NONE type without reference_id (should fail validation)
        data = {
            'reference_type': StockMovement.ReferenceType.INVOICE,
            'warehouse': self.warehouse.id,
            'note': 'Invoice without ID',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reference ID is required')
        
        # Test valid non-NONE type with reference_id
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,
            'reference_id': 456,
            'warehouse': self.warehouse.id,
            'note': 'Packing list with ID',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertIn(response.status_code, [200, 302])
        
        movement = StockMovement.objects.get(note='Packing list with ID')
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.PACKING_LIST)
        self.assertEqual(movement.reference_id, 456)
    
    def test_negative_reference_id_validation(self):
        """Test that negative reference_id is rejected"""
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.INVOICE,
            'reference_id': -123,  # Negative ID should fail
            'warehouse': self.warehouse.id,
            'note': 'Negative reference ID test',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        # Should contain validation error about positive integer
        self.assertContains(response, 'Reference ID must be a positive integer')
    
    def test_zero_reference_id_validation(self):
        """Test that zero reference_id is rejected"""
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.PRODUCTION,
            'reference_id': 0,  # Zero ID should fail
            'warehouse': self.warehouse.id,
            'note': 'Zero reference ID test',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        # Should contain validation error about reference ID being required
        self.assertContains(response, 'Reference ID is required when reference type is PRODUCTION')
    
    def test_note_max_length_validation(self):
        """Test note field maximum length validation"""
        self.client.login(username='testuser', password='testpass')
        
        # Create a note longer than 1000 characters
        long_note = 'A' * 1001
        
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': long_note,
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        # Should contain validation error about max length
        self.assertContains(response, 'Note cannot exceed 1000 characters')
    
    def test_note_whitespace_cleaning(self):
        """Test that note field whitespace is cleaned correctly"""
        self.client.login(username='testuser', password='testpass')
        
        test_cases = [
            ('  Note with spaces  ', 'Note with spaces'),
            ('\t\nNote with tabs and newlines\t\n', 'Note with tabs and newlines'),
            ('  \t\n  ', None),  # Only whitespace becomes None
        ]
        
        for i, (input_note, expected_note) in enumerate(test_cases):
            # Clean up previous movements to avoid unique constraint
            StockMovement.objects.filter(warehouse=self.warehouse).delete()
            
            data = {
                'reference_type': StockMovement.ReferenceType.NONE,
                'warehouse': self.warehouse.id,
                'note': input_note,
            }
            
            response = self.client.post(self.create_url, data)
            self.assertIn(response.status_code, [200, 302])
            
            movement = StockMovement.objects.latest('created_at')
            self.assertEqual(movement.note, expected_note)
    
    def test_note_whitespace_cleaning(self):
        """Test that note field whitespace is cleaned correctly"""
        self.client.login(username='testuser', password='testpass')
        
        test_cases = [
            ('  Note with spaces  ', 'Note with spaces'),
            ('\t\nNote with tabs and newlines\t\n', 'Note with tabs and newlines'),
            ('  \t\n  ', None),  # Only whitespace becomes None
        ]
        
        for i, (input_note, expected_note) in enumerate(test_cases):
            # Clean up previous movements to avoid unique constraint
            StockMovement.objects.filter(warehouse=self.warehouse).delete()
            
            data = {
                'reference_type': StockMovement.ReferenceType.NONE,
                'warehouse': self.warehouse.id,
                'note': input_note,
            }
            
            response = self.client.post(self.create_url, data)
            self.assertIn(response.status_code, [200, 302])
            
            movement = StockMovement.objects.latest('created_at')
            self.assertEqual(movement.note, expected_note)
    
    def test_inactive_warehouse_filtering(self):
        """Test that inactive warehouses are filtered out from form choices"""
        # Create inactive warehouse with shorter code
        inactive_warehouse = Warehouse.objects.create(
            name='Inactive Test Warehouse',
            code='INACT01',  # Shortened to fit validation
            address='123 Inactive Test St',
            is_active=True,  # Create as active first
            created_by=self.user,
            updated_by=self.user
        )
        Warehouse.objects.filter(id=inactive_warehouse.id).update(is_active=False)
        
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(self.create_url)
        form = response.context['form']
        
        # Check that inactive warehouse is not in queryset
        warehouse_choices = form.fields['warehouse'].queryset
        self.assertIn(self.warehouse, warehouse_choices)
        self.assertNotIn(inactive_warehouse, warehouse_choices)


class StockMovementCreateViewErrorHandlingTest(TestCase):
    """Test error handling scenarios for StockMovementCreateView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Error Test Warehouse',
            code='ERRTEST01',
            address='123 Error Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.add_permission = Permission.objects.get(codename='add_stockmovement')
        self.user.user_permissions.add(self.add_permission)
        self.create_url = reverse('inventory:stock-movement-create', args=[self.warehouse.id])
    
    def test_invalid_reference_type(self):
        """Test handling of invalid reference type"""
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'reference_type': 'INVALID_TYPE',
            'warehouse': self.warehouse.id,
            'note': 'Invalid type test',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice')
    
    def test_malformed_data(self):
        """Test handling of malformed data"""
        self.client.login(username='testuser', password='testpass')
        
        # Test with string where integer expected
        data = {
            'reference_type': StockMovement.ReferenceType.INVOICE,
            'reference_id': 'not_a_number',
            'warehouse': self.warehouse.id,
            'note': 'Malformed data test',
        }
        
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a whole number')
    
    # def test_missing_warehouse_in_form_data(self):
    #     """Test handling when warehouse is missing from form data"""
    #     self.client.login(username='testuser', password='testpass')
        
    #     data = {
    #         'reference_type': StockMovement.ReferenceType.NONE,
    #         'note': 'Missing warehouse test',
    #         # warehouse field intentionally omitted
    #     }
        
    #     response = self.client.post(self.create_url, data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'This field is required')
    
    # def test_warehouse_mismatch_in_form_data(self):
    #     """Test handling when form warehouse doesn't match URL warehouse"""
    #     # Create another warehouse
    #     other_warehouse = Warehouse.objects.create(
    #         name='Other Warehouse',
    #         code='OTHER01',
    #         address='123 Other St',
    #         is_active=True,
    #         created_by=self.user,
    #         updated_by=self.user
    #     )
        
    #     self.client.login(username='testuser', password='testpass')
        
    #     data = {
    #         'reference_type': StockMovement.ReferenceType.NONE,
    #         'warehouse': other_warehouse.id,  # Different from URL warehouse
    #         'note': 'Warehouse mismatch test',
    #     }
        
    #     response = self.client.post(self.create_url, data)
    #     self.assertEqual(response.status_code, 200)
    #     # Should contain validation error about warehouse mismatch
    #     self.assertContains(response, 'does not match the warehouse in the URL')


class StockMovementCreateViewHTMXTest(TestCase):
    """Test HTMX-specific functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='htmxuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='HTMX Test Warehouse',
            code='HTMX01',
            address='123 HTMX St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.add_permission = Permission.objects.get(codename='add_stockmovement')
        self.user.user_permissions.add(self.add_permission)
        self.create_url = reverse('inventory:stock-movement-create', args=[self.warehouse.id])
    
    def test_htmx_success_headers(self):
        """Test HTMX success response headers and triggers"""
        self.client.login(username='htmxuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': 'HTMX success test',
        }
        
        response = self.client.post(
            self.create_url, 
            data, 
            HTTP_HX_REQUEST='true'  # Simulate HTMX request
        )
        
        # Check response is successful
        self.assertIn(response.status_code, [200, 302])
        
        # Verify movement was created
        self.assertTrue(StockMovement.objects.filter(note='HTMX success test').exists())
        
        # Verify HTMX trigger was set (if successful creation)
        if response.status_code == 200:
            self.assertEqual(response.get('HX-Trigger'), 'success')
    
    def test_htmx_error_headers(self):
        """Test HTMX error response headers for retargeting"""
        self.client.login(username='htmxuser', password='testpass')
        
        # Send invalid data to trigger form error
        data = {
            'reference_type': StockMovement.ReferenceType.INVOICE,
            'warehouse': self.warehouse.id,
            # Missing reference_id - should cause validation error
        }
        
        response = self.client.post(
            self.create_url, 
            data, 
            HTTP_HX_REQUEST='true'  # Simulate HTMX request
        )
        
        self.assertEqual(response.status_code, 200)
        # Check HTMX error handling headers
        self.assertEqual(response.get('HX-Retarget'), '#stock-movement-form')
        self.assertEqual(response.get('HX-Reswap'), 'innerHTML')
    
    def test_non_htmx_request_handling(self):
        """Test that non-HTMX requests are handled properly"""
        self.client.login(username='htmxuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': 'Non-HTMX test',
        }
        
        # Regular POST request (no HX-Request header)
        response = self.client.post(self.create_url, data)
        self.assertIn(response.status_code, [200, 302])
        
        # Should still create the movement
        self.assertTrue(StockMovement.objects.filter(note='Non-HTMX test').exists())


class StockMovementCreateViewPermissionTest(TestCase):
    """Extended permission testing"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='permuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass')
        
        self.warehouse1 = Warehouse.objects.create(
            name='Warehouse 1',
            code='WH001',
            address='123 Warehouse 1 St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.warehouse2 = Warehouse.objects.create(
            name='Warehouse 2', 
            code='WH002',
            address='123 Warehouse 2 St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.add_permission = Permission.objects.get(codename='add_stockmovement')
        
        # Create warehouse-specific permissions
        from django.contrib.contenttypes.models import ContentType
        warehouse_ct = ContentType.objects.get_for_model(Warehouse)
        
        self.warehouse1_permission = Permission.objects.create(
            codename=f'can_manage_warehouse_{self.warehouse1.id}',
            name=f'Can manage warehouse {self.warehouse1.id}',
            content_type=warehouse_ct,
        )
        
        self.warehouse2_permission = Permission.objects.create(
            codename=f'can_manage_warehouse_{self.warehouse2.id}',
            name=f'Can manage warehouse {self.warehouse2.id}',
            content_type=warehouse_ct,
        )
        
        self.create_url_wh1 = reverse('inventory:stock-movement-create', args=[self.warehouse1.id])
        self.create_url_wh2 = reverse('inventory:stock-movement-create', args=[self.warehouse2.id])
    
    def test_global_permission_allows_all_warehouses(self):
        """Test that global add_stockmovement permission works for all warehouses"""
        self.user.user_permissions.add(self.add_permission)
        self.client.login(username='permuser', password='testpass')
        
        # Should work for warehouse1
        response = self.client.get(self.create_url_wh1)
        self.assertEqual(response.status_code, 200)
        
        # Should work for warehouse2
        response = self.client.get(self.create_url_wh2)
        self.assertEqual(response.status_code, 200)
    
    def test_warehouse_specific_permission_restricted(self):
        """Test that warehouse-specific permission only works for that warehouse"""
        # Give user permission only for warehouse1
        self.user.user_permissions.add(self.warehouse1_permission)
        self.client.login(username='permuser', password='testpass')
        
        # Should work for warehouse1
        response = self.client.get(self.create_url_wh1)
        self.assertEqual(response.status_code, 200)
        
        # Should NOT work for warehouse2
        response = self.client.get(self.create_url_wh2)
        self.assertEqual(response.status_code, 403)
    
    def test_multiple_warehouse_permissions(self):
        """Test user with permissions for multiple warehouses"""
        # Give user permissions for both warehouses
        self.user.user_permissions.add(self.warehouse1_permission, self.warehouse2_permission)
        self.client.login(username='permuser', password='testpass')
        
        # Should work for both warehouses
        response = self.client.get(self.create_url_wh1)
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(self.create_url_wh2)
        self.assertEqual(response.status_code, 200)
    
    def test_permission_inheritance_precedence(self):
        """Test that global permission takes precedence over warehouse-specific"""
        # Give user global permission and warehouse1 permission
        self.user.user_permissions.add(self.add_permission, self.warehouse1_permission)
        self.client.login(username='permuser', password='testpass')
        
        # Should work for all warehouses due to global permission
        response = self.client.get(self.create_url_wh1)
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(self.create_url_wh2)
        self.assertEqual(response.status_code, 200)  # Works due to global permission
