# catalog/tests/item/test_item_create_view.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class ItemCreateViewTest(TestCase):
    """Test cases for ItemCreateView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create user with permission
        self.user_with_permission = User.objects.create_user(
            username='permuser',
            password='testpass123'
        )
        
        # Add permission to create items
        content_type = ContentType.objects.get_for_model(ItemSKU)
        permission = Permission.objects.get(
            codename='add_itemsku',
            content_type=content_type
        )
        self.user_with_permission.user_permissions.add(permission)
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('catalog:item-form')

    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_view_requires_permission(self):
        """Test that view requires add_itemsku permission"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Should redirect to permission denied or return 403
        self.assertIn(response.status_code, [302, 403])

    def test_view_with_permission(self):
        """Test view access with proper permission"""
        self.client.login(username='permuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item/item-form.html')

    def test_template_used(self):
        """Test correct template is used"""
        self.client.login(username='permuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertTemplateUsed(response, 'catalog/item/item-form.html')

    def test_form_in_context(self):
        """Test that form is in context"""
        self.client.login(username='permuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertIn('form', response.context)
        # CreateView doesn't have object until form is saved, so we check that form exists
        self.assertIsNotNone(response.context['form'])

    def test_successful_item_creation(self):
        """Test successful item creation"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'NEW001',
            'name': 'New Test Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,  # Use RAW type instead of PRODUCT
            'status': ItemSKU.Status.ACTIVE,
            'category': self.category.id,
            'note': 'Test note'
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should redirect to item list
        self.assertRedirects(response, reverse('catalog:item-list'))
        
        # Check item was created
        item = ItemSKU.objects.get(sku_code='NEW001')
        self.assertEqual(item.name, 'New Test Item')
        self.assertEqual(item.created_by, self.user_with_permission)
        self.assertEqual(item.updated_by, self.user_with_permission)

    def test_duplicate_sku_code_error(self):
        """Test creation with duplicate SKU code"""
        # Create an existing item
        ItemSKU.objects.create(
            sku_code='DUPLICATE001',
            name='Existing Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            created_by=self.user_with_permission,
            updated_by=self.user_with_permission
        )
        
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'DUPLICATE001',  # Same SKU code
            'name': 'New Test Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should stay on form page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')  # Check for duplicate error message

    def test_form_validation_errors(self):
        """Test form validation with invalid data"""
        self.client.login(username='permuser', password='testpass123')
        
        # Submit form with missing required fields
        form_data = {
            'sku_code': '',  # Required field
            'name': '',      # Required field
            'unit': '',      # Required field
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should stay on form page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')  # Check for required field errors

    def test_success_message(self):
        """Test success message is shown after creation"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'SUCCESS001',
            'name': 'Success Test Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data, follow=True)
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('Success Test Item', str(messages[0]))
        self.assertIn('created successfully', str(messages[0]))

    def test_form_with_category(self):
        """Test creating item with category"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'CAT001',
            'name': 'Item with Category',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
            'category': self.category.id,
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, reverse('catalog:item-list'))
        
        item = ItemSKU.objects.get(sku_code='CAT001')
        self.assertEqual(item.category, self.category)

    def test_form_with_product_type_draft_status(self):
        """Test creating PRODUCT type item with DRAFT status (valid)"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'PROD001',
            'name': 'Product Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.PRODUCT,
            'status': ItemSKU.Status.DRAFT,  # PRODUCT should start as DRAFT
            'category': self.category.id,
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, reverse('catalog:item-list'))
        
        item = ItemSKU.objects.get(sku_code='PROD001')
        self.assertEqual(item.type, ItemSKU.Type.PRODUCT)
        self.assertEqual(item.status, ItemSKU.Status.DRAFT)

    def test_form_without_category(self):
        """Test creating item without category (optional field)"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'NOCAT001',
            'name': 'Item without Category',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, reverse('catalog:item-list'))
        
        item = ItemSKU.objects.get(sku_code='NOCAT001')
        self.assertIsNone(item.category)

    def test_business_logic_validation_error(self):
        """Test handling of business logic validation errors"""
        self.client.login(username='permuser', password='testpass123')
        
        # This should trigger business logic validation
        # Try to create a PRODUCT with ACTIVE status (should require DRAFT first)
        form_data = {
            'sku_code': 'BUSINESS001',
            'name': 'Business Rule Test Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.PRODUCT,  # PRODUCT type
            'status': ItemSKU.Status.ACTIVE,  # ACTIVE status (should be DRAFT)
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should stay on form page if business logic validation fails
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'should typically start as DRAFT')  # Check for business rule error

    def test_next_url_redirect(self):
        """Test that view redirects to next URL when provided"""
        self.client.login(username='permuser', password='testpass123')
        
        # Test with next URL parameter
        next_url = reverse('catalog:item-list')
        url_with_next = f"{self.url}?next={next_url}"
        
        form_data = {
            'sku_code': 'NEXT001',
            'name': 'Next URL Test Item',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(url_with_next, form_data)
        
        # Should redirect to the next URL
        self.assertRedirects(response, next_url)

    def test_next_url_in_context(self):
        """Test that next URL is passed to template context"""
        self.client.login(username='permuser', password='testpass123')
        
        next_url = reverse('catalog:item-list')
        url_with_next = f"{self.url}?next={next_url}"
        
        response = self.client.get(url_with_next)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['next_url'], next_url)

    def test_default_redirect_without_next_url(self):
        """Test default redirect when no next URL is provided"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'DEFAULT001',
            'name': 'Default Redirect Test',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should redirect to default item list
        self.assertRedirects(response, reverse('catalog:item-list'))
