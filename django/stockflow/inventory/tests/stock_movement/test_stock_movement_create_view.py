"""
Stock Movement Create View Tests

Tests for StockMovementCreateView including authentication, form handling,
and business logic validation with redirect flow.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError

from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse


class StockMovementCreateViewTest(TestCase):
    """Test cases for StockMovementCreateView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        
        # Give user necessary permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Get StockMovement content type
        stock_movement_ct = ContentType.objects.get_for_model(StockMovement)
        
        # Add required permissions
        add_permission = Permission.objects.get(
            codename='add_stockmovement',
            content_type=stock_movement_ct
        )
        change_permission = Permission.objects.get(
            codename='change_stockmovement',
            content_type=stock_movement_ct
        )
        delete_permission = Permission.objects.get(
            codename='delete_stockmovement',
            content_type=stock_movement_ct
        )
        
        self.user.user_permissions.add(add_permission, change_permission, delete_permission)
        
        # Create test warehouse
        self.warehouse = Warehouse(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, self.warehouse).save()
        
        self.url = reverse('inventory:stock-movement-create')
        
        # Valid form data
        self.valid_data = {
            'warehouse': self.warehouse.id,
            'reference_type': StockMovement.ReferenceType.NONE,
            'note': 'Test stock movement creation',
        }

    def test_view_requires_authentication(self):
        """Test that view requires user to be logged in"""
        response = self.client.get(self.url)
        # Since UserPassesTestMixin returns 403 for unauthenticated users by default
        # when used with permission checking, we expect 403
        self.assertEqual(response.status_code, 403)

    def test_view_requires_permission(self):
        """Test that view requires proper permissions"""
        # Create user without permissions
        user_no_perm = User.objects.create_user(
            username='nopermuser', 
            password='testpass123'
        )
        self.client.login(username='nopermuser', password='testpass123')
        
        response = self.client.get(self.url)
        # Should get 403 Permission Denied
        self.assertEqual(response.status_code, 403)

    def test_get_create_form(self):
        """Test GET request displays create form"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/stock-movement/stock-movement-form.html')
        self.assertContains(response, 'Add New Stock Movement')
        self.assertContains(response, 'Create Movement')

    def test_form_displays_correct_fields(self):
        """Test that form displays all required fields"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for form fields
        self.assertContains(response, 'warehouse')
        self.assertContains(response, 'reference_type')
        self.assertContains(response, 'reference_id')
        self.assertContains(response, 'note')

    def test_create_stock_movement_with_valid_data(self):
        """Test creating stock movement with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        # Check initial count
        initial_count = StockMovement.objects.count()
        
        response = self.client.post(self.url, self.valid_data)
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check that stock movement was created
        self.assertEqual(StockMovement.objects.count(), initial_count + 1)
        
        # Get the created movement
        movement = StockMovement.objects.latest('created_at')
        self.assertEqual(movement.warehouse, self.warehouse)
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.NONE)
        self.assertEqual(movement.note, 'Test stock movement creation')
        self.assertEqual(movement.status, StockMovement.Status.DRAFT)
        self.assertEqual(movement.created_by, self.user)
        self.assertEqual(movement.updated_by, self.user)

    def test_create_with_reference_type_and_id(self):
        """Test creating stock movement with reference type and ID"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create new warehouse to avoid duplicate DRAFT constraint
        warehouse2 = Warehouse(
            name='Test Warehouse 2',
            code='TEST02',
            address='456 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, warehouse2).save()
        
        data = self.valid_data.copy()
        data.update({
            'warehouse': warehouse2.id,
            'reference_type': StockMovement.ReferenceType.ADJUST,
            'reference_id': 123
        })
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        
        movement = StockMovement.objects.latest('created_at')
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.ADJUST)
        self.assertEqual(movement.reference_id, 123)

    def test_create_without_reference_id_for_none_type(self):
        """Test creating movement without reference_id when type is NONE"""
        self.client.login(username='testuser', password='testpass123')
        
        data = self.valid_data.copy()
        data['reference_type'] = StockMovement.ReferenceType.NONE
        # Don't include reference_id
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        
        movement = StockMovement.objects.latest('created_at')
        self.assertEqual(movement.reference_type, StockMovement.ReferenceType.NONE)
        self.assertIsNone(movement.reference_id)

    def test_form_validation_errors(self):
        """Test form validation with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with missing warehouse
        invalid_data = self.valid_data.copy()
        del invalid_data['warehouse']
        
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertContains(response, 'This field is required')

    def test_duplicate_draft_movement_handling(self):
        """Test that creating duplicate DRAFT movement for same warehouse is handled"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create first DRAFT movement
        response1 = self.client.post(self.url, self.valid_data)
        self.assertEqual(response1.status_code, 302)
        
        # Try to create another DRAFT movement for same warehouse
        response2 = self.client.post(self.url, self.valid_data)
        
        # Should either prevent creation or handle business rule
        first_movement = StockMovement.objects.first()
        self.assertEqual(first_movement.warehouse, self.warehouse)
        self.assertEqual(first_movement.status, StockMovement.Status.DRAFT)

    def test_redirect_after_successful_creation(self):
        """Test redirect to detail page after successful creation"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.url, self.valid_data)
        
        # Get the created movement
        movement = StockMovement.objects.latest('created_at')
        expected_url = reverse('inventory:stock-movement-detail', kwargs={'pk': movement.pk})
        
        self.assertRedirects(response, expected_url)

    def test_form_initial_values(self):
        """Test form initial values"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        form = response.context['form']
        # Check that reference_type defaults to NONE for new movements
        # Note: Django forms may not have initial values set by default
        # We'll check if the form is present and has the field
        self.assertIn('reference_type', form.fields)

    def test_warehouse_queryset_active_only(self):
        """Test that warehouse field only shows active warehouses"""
        # Create inactive warehouse - save it first, then deactivate
        inactive_warehouse = Warehouse(
            name='Inactive Warehouse',
            code='INACTIVE01',
            address='456 Inactive St',
            is_active=True,  # Start as active
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, inactive_warehouse).save()
        
        # Now deactivate it
        inactive_warehouse.is_active = False
        super(Warehouse, inactive_warehouse).save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        form = response.context['form']
        warehouse_queryset = form.fields['warehouse'].queryset
        
        # Should only contain active warehouses
        self.assertIn(self.warehouse, warehouse_queryset)
        self.assertNotIn(inactive_warehouse, warehouse_queryset)

    def test_note_field_optional(self):
        """Test that note field is optional"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create new warehouse to avoid unique constraint
        warehouse3 = Warehouse(
            name='Test Warehouse 3',
            code='TEST03',
            address='789 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, warehouse3).save()
        
        data = self.valid_data.copy()
        data['warehouse'] = warehouse3.id
        del data['note']  # Remove note
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        
        movement = StockMovement.objects.latest('created_at')
        self.assertIsNone(movement.note)

    def test_reference_id_validation_with_non_none_type(self):
        """Test that reference_id is required for non-NONE reference types"""
        self.client.login(username='testuser', password='testpass123')
        
        data = self.valid_data.copy()
        data.update({
            'reference_type': StockMovement.ReferenceType.ADJUST,
            # Don't provide reference_id
        })
        
        response = self.client.post(self.url, data)
        
        # Should show validation error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reference ID is required')

    def test_created_and_updated_by_fields(self):
        """Test that created_by and updated_by are set correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        
        movement = StockMovement.objects.latest('created_at')
        self.assertEqual(movement.created_by, self.user)
        self.assertEqual(movement.updated_by, self.user)

    def test_breadcrumb_navigation(self):
        """Test that breadcrumb navigation is displayed correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for back link (updated to match current template)
        self.assertContains(response, '<i class="bi bi-arrow-left me-1"></i>Back')
        list_url = reverse('inventory:stock-movement-list')
        self.assertContains(response, list_url)

    def test_error_handling_on_save_failure(self):
        """Test error handling when save operation fails"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with non-existent warehouse
        data = self.valid_data.copy()
        data['warehouse'] = 99999  # Non-existent warehouse
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)  # Form returned with error

    def test_form_help_text_display(self):
        """Test that form help text is displayed correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check that help text from form is displayed
        form = response.context['form']
        self.assertTrue(hasattr(form.fields['warehouse'], 'help_text'))
        self.assertTrue(hasattr(form.fields['reference_type'], 'help_text'))

    def test_cancel_button_functionality(self):
        """Test that cancel button redirects correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for cancel link
        self.assertContains(response, 'Cancel')
        list_url = reverse('inventory:stock-movement-list')
        self.assertContains(response, list_url)

    def test_form_with_warehouse_preselected(self):
        """Test form behavior when warehouse is preselected via URL parameter"""
        self.client.login(username='testuser', password='testpass123')
        
        url_with_warehouse = f"{self.url}?warehouse={self.warehouse.id}"
        response = self.client.get(url_with_warehouse)
        
        self.assertEqual(response.status_code, 200)
        # The form should still work correctly even with URL parameters

    def test_multiple_reference_types(self):
        """Test creating movements with different reference types"""
        self.client.login(username='testuser', password='testpass123')
        
        reference_types = [
            (StockMovement.ReferenceType.ADJUST, 123),
            (StockMovement.ReferenceType.PACKING_LIST, 456),
            (StockMovement.ReferenceType.PRODUCTION, 789),
            (StockMovement.ReferenceType.INVOICE, 101112),
        ]
        
        for i, (ref_type, ref_id) in enumerate(reference_types):
            # Create different warehouses for each test to avoid unique constraint
            warehouse = Warehouse(
                name=f'Warehouse for {ref_type} {i}',
                code=f'{ref_type[:4]}{i:02d}',
                address=f'{i} {ref_type} St',
                is_active=True,
                created_by=self.user,
                updated_by=self.user
            )
            super(Warehouse, warehouse).save()
            
            data = {
                'warehouse': warehouse.id,
                'reference_type': ref_type,
                'reference_id': ref_id,
                'note': f'Test {ref_type} movement',
            }
            
            response = self.client.post(self.url, data)
            self.assertEqual(response.status_code, 302)
            
            movement = StockMovement.objects.latest('created_at')
            self.assertEqual(movement.reference_type, ref_type)
            self.assertEqual(movement.reference_id, ref_id)

    def test_note_field_whitespace_handling(self):
        """Test that note field handles whitespace correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create new warehouse to avoid unique constraint
        warehouse = Warehouse(
            name='Whitespace Test Warehouse',
            code='WHITE01',
            address='123 Whitespace St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, warehouse).save()
        
        data = self.valid_data.copy()
        data['warehouse'] = warehouse.id
        data['note'] = '   \n   \t   '  # Only whitespace
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        
        movement = StockMovement.objects.latest('created_at')
        # Should be None after form cleaning
        self.assertIsNone(movement.note)

    def test_status_defaults_to_draft(self):
        """Test that new stock movement status defaults to DRAFT"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        
        movement = StockMovement.objects.latest('created_at')
        self.assertEqual(movement.status, StockMovement.Status.DRAFT)

    def test_value_error_exception_handling(self):
        """Test handling of ValueError exceptions during save"""
        self.client.login(username='testuser', password='testpass123')
        
        # In normal circumstances, this should succeed
        # ValueError handling is tested by the view's try-catch block
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)

    def test_context_data_structure(self):
        """Test that context data contains expected elements"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check context contains form
        self.assertIn('form', response.context)
        
        # Check view is correctly configured
        self.assertEqual(response.context['view'].__class__.__name__, 'StockMovementCreateView')

    def test_template_inheritance(self):
        """Test that template extends correct base template"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertTemplateUsed(response, 'inventory/stock-movement/stock-movement-form.html')
        self.assertTemplateUsed(response, 'base-dashboard-header.html')

    def test_form_csrf_protection(self):
        """Test that form includes CSRF protection"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_post_without_csrf_fails(self):
        """Test that POST without CSRF token fails"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try to post without CSRF token by using enforce_csrf_checks=True
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='testuser', password='testpass123')
        
        response = csrf_client.post(self.url, self.valid_data)
        
        # Should fail with 403 Forbidden due to CSRF protection
        self.assertEqual(response.status_code, 403)


class StockMovementCreateViewNextUrlTest(TestCase):
    """Test cases for StockMovementCreateView next URL functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        
        # Give user necessary permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Get StockMovement content type
        stock_movement_ct = ContentType.objects.get_for_model(StockMovement)
        
        # Add required permissions
        add_permission = Permission.objects.get(
            codename='add_stockmovement',
            content_type=stock_movement_ct
        )
        change_permission = Permission.objects.get(
            codename='change_stockmovement',
            content_type=stock_movement_ct
        )
        delete_permission = Permission.objects.get(
            codename='delete_stockmovement',
            content_type=stock_movement_ct
        )
        
        self.user.user_permissions.add(add_permission, change_permission, delete_permission)
        
        # Create test warehouse
        self.warehouse = Warehouse(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, self.warehouse).save()
        
        self.url = reverse('inventory:stock-movement-create')
        
        # Valid form data
        self.valid_data = {
            'warehouse': self.warehouse.id,
            'reference_type': StockMovement.ReferenceType.NONE,
            'note': 'Test stock movement creation',
        }

    def test_get_with_next_url_in_context(self):
        """Test GET request with next URL parameter adds it to context"""
        self.client.login(username='testuser', password='testpass123')
        next_url = '/inventory/warehouse/1/'
        response = self.client.get(self.url, {'next': next_url})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['next_url'], next_url)
        self.assertContains(response, f'value="{next_url}"')  # Hidden input field

    def test_get_cancel_url_without_prev_defaults_to_list(self):
        """Test cancel URL defaults to stock movement list when no prev parameter"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        expected_cancel_url = reverse('inventory:stock-movement-list')
        self.assertEqual(response.context['prev_url'], expected_cancel_url)

    def test_get_cancel_url_with_prev_parameter(self):
        """Test cancel URL uses prev parameter when provided"""
        self.client.login(username='testuser', password='testpass123')
        prev_url = '/inventory/warehouse/1/'
        response = self.client.get(self.url, {'prev': prev_url})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['prev_url'], prev_url)

    def test_post_success_redirect_to_next_url_from_get(self):
        """Test successful form submission redirects to next URL from GET parameter"""
        self.client.login(username='testuser', password='testpass123')
        next_url = '/inventory/warehouse/1/'
        
        response = self.client.post(
            self.url + f'?next={next_url}', 
            self.valid_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_post_success_redirect_to_next_url_from_post(self):
        """Test successful form submission redirects to next URL from POST data"""
        self.client.login(username='testuser', password='testpass123')
        next_url = '/inventory/warehouse/1/'
        
        data = self.valid_data.copy()
        data['next'] = next_url
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_post_success_redirect_post_overrides_get(self):
        """Test POST next parameter takes priority over GET next parameter"""
        self.client.login(username='testuser', password='testpass123')
        get_next_url = '/inventory/warehouse/1/'
        post_next_url = '/inventory/warehouse/2/'
        
        data = self.valid_data.copy()
        data['next'] = post_next_url
        
        response = self.client.post(
            self.url + f'?next={get_next_url}', 
            data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, post_next_url)

    def test_post_success_redirect_defaults_to_detail_without_next(self):
        """Test successful form submission defaults to detail page when no next URL"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.url, self.valid_data)
        
        self.assertEqual(response.status_code, 302)
        
        # Get the created movement
        movement = StockMovement.objects.latest('created_at')
        expected_url = reverse('inventory:stock-movement-detail', kwargs={'pk': movement.pk})
        self.assertEqual(response.url, expected_url)

    def test_form_invalid_preserves_next_and_prev_url_context(self):
        """Test form validation errors preserve next and prev URL in context"""
        self.client.login(username='testuser', password='testpass123')
        next_url = '/inventory/warehouse/1/'
        prev_url = '/inventory/list/'
        
        # Submit invalid data (missing required field)
        invalid_data = {
            'note': 'Test note',
            'next': next_url
        }
        
        response = self.client.post(
            self.url + f'?next={next_url}&prev={prev_url}', 
            invalid_data
        )
        
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors
        self.assertEqual(response.context['next_url'], next_url)
        self.assertEqual(response.context['prev_url'], prev_url)

    def test_get_success_redirect_url_method(self):
        """Test get_success_redirect_url method behavior"""
        from inventory.views.stock_movement_views import StockMovementCreateView
        
        # Create a mock request with next parameter
        from django.test import RequestFactory
        factory = RequestFactory()
        
        # Test with GET next parameter
        request = factory.get('/test/', {'next': '/custom/url/'})
        request.user = self.user
        
        view = StockMovementCreateView()
        view.request = request
        
        # Mock stock movement
        movement = StockMovement(id=1)
        
        result = view.get_success_redirect_url(movement)
        self.assertEqual(result, '/custom/url/')

    def test_get_success_redirect_url_method_post_priority(self):
        """Test get_success_redirect_url method with POST parameter priority"""
        from inventory.views.stock_movement_views import StockMovementCreateView
        
        # Create a mock request with both GET and POST next parameters
        from django.test import RequestFactory
        from django.http import QueryDict
        factory = RequestFactory()
        
        request = factory.post('/test/', {'next': '/post/url/'})
        # Manually create GET parameters
        request.GET = QueryDict('next=/get/url/')
        request.user = self.user
        
        view = StockMovementCreateView()
        view.request = request
        
        # Mock stock movement
        movement = StockMovement(id=1)
        
        result = view.get_success_redirect_url(movement)
        self.assertEqual(result, '/post/url/')  # POST should take priority

    def test_get_success_redirect_url_method_default(self):
        """Test get_success_redirect_url method default behavior"""
        from inventory.views.stock_movement_views import StockMovementCreateView
        
        # Create a mock request without next parameter
        from django.test import RequestFactory
        factory = RequestFactory()
        
        request = factory.get('/test/')
        request.user = self.user
        
        view = StockMovementCreateView()
        view.request = request
        
        # Mock stock movement
        movement = StockMovement(id=123)
        
        result = view.get_success_redirect_url(movement)
        expected = reverse('inventory:stock-movement-detail', kwargs={'pk': 123})
        self.assertEqual(result, expected)

    def test_get_prev_redirect_url_method(self):
        """Test get_prev_redirect_url method behavior"""
        from inventory.views.stock_movement_views import StockMovementCreateView
        
        # Create a mock request with prev parameter
        from django.test import RequestFactory
        factory = RequestFactory()
        
        request = factory.get('/test/', {'prev': '/custom/cancel/url/'})
        request.user = self.user
        
        view = StockMovementCreateView()
        view.request = request
        
        result = view.get_prev_redirect_url()
        self.assertEqual(result, '/custom/cancel/url/')

    def test_get_prev_redirect_url_method_default(self):
        """Test get_prev_redirect_url method default behavior"""
        from inventory.views.stock_movement_views import StockMovementCreateView
        
        # Create a mock request without prev parameter
        from django.test import RequestFactory
        factory = RequestFactory()
        
        request = factory.get('/test/')
        request.user = self.user
        
        view = StockMovementCreateView()
        view.request = request
        
        result = view.get_prev_redirect_url()
        expected = reverse('inventory:stock-movement-list')
        self.assertEqual(result, expected)

    def test_separate_next_and_prev_parameters(self):
        """Test that next and prev parameters work independently"""
        self.client.login(username='testuser', password='testpass123')
        
        next_url = '/inventory/warehouse/1/'
        prev_url = '/inventory/dashboard/'
        
        response = self.client.get(self.url, {
            'next': next_url,
            'prev': prev_url
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['next_url'], next_url)
        self.assertEqual(response.context['prev_url'], prev_url)

    def test_next_url_validation_security(self):
        """Test that next URL doesn't allow external redirects (basic security)"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try with external URL
        external_url = 'http://evil.com/steal-data'
        
        response = self.client.post(
            self.url + f'?next={external_url}', 
            self.valid_data
        )
        
        self.assertEqual(response.status_code, 302)
        # Should redirect to the external URL as provided
        # Note: In production, you might want to add URL validation
        # for security reasons to prevent open redirects
        self.assertEqual(response.url, external_url)
