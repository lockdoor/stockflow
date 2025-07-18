from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.forms.item_form import ItemForm
from django.core.exceptions import ValidationError


class ItemCreateViewTest(TestCase):
    """Test suite for the ItemCreateView"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user with necessary permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Assign required permissions
        permission = Permission.objects.get(codename='add_itemsku')
        self.user.user_permissions.add(permission)
        
        # Create user without permissions for testing permission checks
        self.unprivileged_user = User.objects.create_user(
            username='unprivileged',
            password='testpassword'
        )

        # Create an active category for testing
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user,
            is_active=True
        )
        
        # URL for creating items
        self.create_url = reverse('catalog:item-create')
        
        # Valid form data
        self.valid_item_data = {
            'sku_code': 'TEST-001',
            'name': 'Test Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.PRODUCT,
            'category': self.category.id
        }

    def test_login_required(self):
        """Test that login is required to access the view"""
        # Attempt to access without login
        response = self.client.get(self.create_url)
        
        # Should redirect to login page (status code 302 is a redirect)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)

    def test_permission_required(self):
        """Test that proper permission is required"""
        # Log in as unprivileged user
        self.client.login(username='unprivileged', password='testpassword')
        
        # Attempt to access with login but without permission
        response = self.client.get(self.create_url)
        
        # Should return forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_get_create_form(self):
        """Test that the view returns the correct form"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Get the form
        response = self.client.get(self.create_url)
        
        # Should return success
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ItemForm)
        self.assertTemplateUsed(response, 'catalog/item/partials/item-form.html')
    
    def test_create_item_success(self):
        """Test that an item can be created successfully"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Post valid data with explicit status to avoid any default value issues
        valid_data = self.valid_item_data.copy()
        valid_data['status'] = ItemSKU.Status.DRAFT
        
        response = self.client.post(self.create_url, valid_data, HTTP_HX_REQUEST='true')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        
        # Verify item was created in database
        self.assertTrue(ItemSKU.objects.filter(sku_code='TEST-001').exists())
        item = ItemSKU.objects.get(sku_code='TEST-001')
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.created_by, self.user)
        self.assertEqual(item.updated_by, self.user)
    
    def test_create_item_with_invalid_data(self):
        """Test handling of invalid form data"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Post invalid data (missing required field)
        invalid_data = self.valid_item_data.copy()
        invalid_data.pop('name')
        response = self.client.post(self.create_url, invalid_data, HTTP_HX_REQUEST='true')
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")
        self.assertContains(response, "Item name is required")
        
        # Verify no item was created
        self.assertFalse(ItemSKU.objects.filter(sku_code='TEST-001').exists())
        
    def test_create_raw_item_with_draft_status(self):
        """Test handling of business logic validation error (raw material cannot be draft)"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Post data with invalid business logic (raw material with draft status)
        invalid_data = self.valid_item_data.copy()
        invalid_data['type'] = ItemSKU.Type.RAW
        invalid_data['status'] = ItemSKU.Status.DRAFT
        
        response = self.client.post(self.create_url, invalid_data, HTTP_HX_REQUEST='true')
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        
        # Check for the business logic error message
        self.assertContains(response, "Raw materials cannot be in DRAFT status")
        
        # Verify no item was created
        self.assertFalse(ItemSKU.objects.filter(sku_code='TEST-001').exists())
        
    def test_create_item_with_inactive_category(self):
        """Test handling of business logic validation error (inactive category)"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Create an inactive category
        inactive_category = Category.objects.create(
            name='Inactive Category',
            created_by=self.user,
            updated_by=self.user,
            is_active=False
        )
        
        # Post data with invalid business logic (inactive category)
        invalid_data = self.valid_item_data.copy()
        invalid_data['category'] = inactive_category.id
        invalid_data['status'] = ItemSKU.Status.DRAFT  # Ensure status is set
        
        response = self.client.post(self.create_url, invalid_data, HTTP_HX_REQUEST='true')
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        
        # The form shows a validation error but the exact message may vary
        # It could be "Select a valid choice" because inactive categories are filtered out of choices
        self.assertContains(response, "Select a valid choice")
        
        # Verify no item was created
        self.assertFalse(ItemSKU.objects.filter(sku_code='TEST-001').exists())
    
    def test_htmx_response_handling(self):
        """Test proper HTMX response handling"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Test HTMX request
        response = self.client.get(self.create_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item/partials/item-form.html')
