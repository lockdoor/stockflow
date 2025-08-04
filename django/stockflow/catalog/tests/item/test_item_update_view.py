# catalog/tests/item/test_item_update_view.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class ItemUpdateViewTest(TestCase):
    """Test cases for ItemUpdateView"""

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
        
        # Add permission to change items
        content_type = ContentType.objects.get_for_model(ItemSKU)
        permission = Permission.objects.get(
            codename='change_itemsku',
            content_type=content_type
        )
        self.user_with_permission.user_permissions.add(permission)
        
        # Create test categories
        self.category1 = Category.objects.create(
            name='Test Category 1',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.category2 = Category.objects.create(
            name='Test Category 2',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item
        self.item = ItemSKU.objects.create(
            sku_code='UPDATE001',
            name='Original Item Name',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.category1,
            note='Original note',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('catalog:item-edit-form', kwargs={'pk': self.item.pk})

    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_view_requires_permission(self):
        """Test that view requires change_itemsku permission"""
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

    def test_form_pre_populated(self):
        """Test that form is pre-populated with existing data"""
        self.client.login(username='permuser', password='testpass123')
        response = self.client.get(self.url)
        
        form = response.context['form']
        self.assertEqual(form.initial.get('sku_code') or form.instance.sku_code, 'UPDATE001')
        self.assertEqual(form.initial.get('name') or form.instance.name, 'Original Item Name')
        self.assertEqual(form.initial.get('unit') or form.instance.unit, 'pcs')
        self.assertEqual(form.initial.get('type') or form.instance.type, ItemSKU.Type.RAW)

    def test_successful_item_update(self):
        """Test successful item update"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'UPDATE001',  # Keep same SKU
            'name': 'Updated Item Name',
            'unit': 'kg',
            'type': ItemSKU.Type.RAW,  # Keep as RAW to avoid validation issues
            'status': ItemSKU.Status.ACTIVE,
            'category': self.category2.id,
            'note': 'Updated note'
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should redirect to item detail (new default behavior)
        self.assertRedirects(response, reverse('catalog:item-detail', kwargs={'pk': self.item.pk}))
        
        # Check item was updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Updated Item Name')
        self.assertEqual(self.item.unit, 'kg')
        self.assertEqual(self.item.type, ItemSKU.Type.RAW)  # Updated to RAW
        self.assertEqual(self.item.category, self.category2)
        self.assertEqual(self.item.note, 'Updated note')
        self.assertEqual(self.item.updated_by, self.user_with_permission)
        # created_by should remain unchanged
        self.assertEqual(self.item.created_by, self.user)

    def test_update_with_duplicate_sku_code(self):
        """Test update with SKU code that belongs to another item"""
        # Create another item
        other_item = ItemSKU.objects.create(
            sku_code='OTHER001',
            name='Other Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'OTHER001',  # SKU code that belongs to another item
            'name': 'Updated Item Name',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should stay on form page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')  # Check for duplicate error message

    def test_update_keeping_same_sku_code(self):
        """Test update keeping the same SKU code (should be allowed)"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'UPDATE001',  # Same SKU code
            'name': 'Updated Item Name',
            'unit': 'kg',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should succeed
        self.assertRedirects(response, reverse('catalog:item-detail', kwargs={'pk': self.item.pk}))
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.sku_code, 'UPDATE001')
        self.assertEqual(self.item.name, 'Updated Item Name')

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
        """Test success message is shown after update"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'UPDATE001',
            'name': 'Updated Item Name',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data, follow=True)
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('Updated Item Name', str(messages[0]))
        self.assertIn('updated successfully', str(messages[0]))

    def test_remove_category(self):
        """Test removing category from item"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'UPDATE001',
            'name': 'Updated Item Name',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
            'category': '',  # Empty category
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, reverse('catalog:item-detail', kwargs={'pk': self.item.pk}))
        
        self.item.refresh_from_db()
        self.assertIsNone(self.item.category)

    def test_change_status(self):
        """Test changing item status"""
        self.client.login(username='permuser', password='testpass123')
        
        form_data = {
            'sku_code': 'UPDATE001',
            'name': 'Original Item Name',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.INACTIVE,  # Change to inactive
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, reverse('catalog:item-detail', kwargs={'pk': self.item.pk}))
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, ItemSKU.Status.INACTIVE)

    def test_update_nonexistent_item(self):
        """Test updating non-existent item returns 404"""
        nonexistent_url = reverse('catalog:item-edit-form', kwargs={'pk': 99999})
        
        self.client.login(username='permuser', password='testpass123')
        response = self.client.get(nonexistent_url)
        
        self.assertEqual(response.status_code, 404)

    def test_business_logic_validation_error(self):
        """Test handling of business logic validation errors during update"""
        self.client.login(username='permuser', password='testpass123')
        
        # This should trigger business logic validation
        # Try to change item type which is not allowed
        form_data = {
            'sku_code': 'UPDATE001',
            'name': 'Updated Item Name',
            'unit': 'pcs', 
            'type': ItemSKU.Type.PRODUCT,  # Change from RAW to PRODUCT (not allowed)
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should stay on form page if business logic validation fails
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Item type cannot be changed once set')  # Check for type change error

    def test_next_url_redirect(self):
        """Test that view redirects to next URL when provided"""
        self.client.login(username='permuser', password='testpass123')
        
        # Test with next URL parameter
        next_url = reverse('catalog:item-list')
        url_with_next = f"{self.url}?next={next_url}"
        
        form_data = {
            'sku_code': 'UPDATE001',
            'name': 'Updated for Next URL Test',
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
            'sku_code': 'UPDATE001',
            'name': 'Default Redirect Test',
            'unit': 'pcs',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.ACTIVE,
        }
        
        response = self.client.post(self.url, form_data)
        
        # Should redirect to default item detail page
        self.assertRedirects(response, reverse('catalog:item-detail', kwargs={'pk': self.item.pk}))
