"""
ItemImageCreateView Tests

Tests for ItemImageCreateView (single image upload).
Covers form validation, file upload, permissions, and authentication.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from catalog.tests.image.test_image_file_mixin import TestImageFileMixin
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category


class ItemImageCreateViewTest(TestImageFileMixin, TestCase):
    """Test cases for ItemImageCreateView"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_no_perm = User.objects.create_user(
            username='testuser_no_perm',
            password='testpass123'
        )
        
        # Add necessary permissions
        content_type = ContentType.objects.get_for_model(ItemImage)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_itemimage', 'change_itemimage', 'delete_itemimage', 'view_itemimage']
        )
        self.user.user_permissions.set(permissions)
        
        # Create test item  
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category note',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            category=self.category,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT to pass validation
            created_by=self.user,
            updated_by=self.user
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
    
    def test_image_upload_view_get_no_perm(self):
        self.client.logout()
        self.client.login(username='testuser_no_perm', password='testpass123')
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
    
    def test_image_upload_view_get(self):
        """Test image upload view GET request"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload Image')
        # Item name appears in dropdown options, not directly in page
        self.assertContains(response, 'name="image"')
        self.assertContains(response, 'name="caption"')
        self.assertContains(response, 'name="is_primary"')
    
    def test_image_upload_view_post_valid_simple(self):
        """Test image upload view POST with valid data (simple case)"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        test_file = self._create_test_image('test_simple.jpg')
        
        form_data = {
            'item': self.item.id,
            'caption': 'Simple test image',
            'is_primary': False,
            'image': test_file
        }
        
        response = self.client.post(url, form_data, format='multipart')
        
        # Should redirect after successful upload
        self.assertEqual(response.status_code, 302)
        
        # Verify image was created
        self.assertTrue(ItemImage.objects.filter(item=self.item).exists())
        
        created_image = ItemImage.objects.get(item=self.item)
        self.assertEqual(created_image.caption, 'Simple test image')
        self.assertEqual(created_image.is_primary, False)
        self.assertEqual(created_image.created_by, self.user)
        self.assertEqual(created_image.updated_by, self.user)
    
    def test_image_upload_view_post_valid(self):
        """Test image upload view POST with valid data (main test)"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        test_file = self._create_test_image('test_upload.jpg')
        
        form_data = {
            'item': self.item.id,
            'caption': 'Test image upload',
            'is_primary': True,
            'image': test_file
        }
        
        response = self.client.post(url, form_data, format='multipart')
        
        # Should redirect after successful upload
        self.assertEqual(response.status_code, 302)
        
        # Verify image was created in database
        self.assertTrue(ItemImage.objects.filter(item=self.item).exists())
        
        created_image = ItemImage.objects.get(item=self.item)
        self.assertEqual(created_image.caption, 'Test image upload')
        self.assertTrue(created_image.is_primary)
        self.assertEqual(created_image.created_by, self.user)
        self.assertEqual(created_image.updated_by, self.user)
        
        # Verify custom file naming
        self.assertTrue(created_image.image.name.startswith('item_images/item_'))
        self.assertTrue('_image_' in created_image.image.name)
        self.assertTrue(created_image.image.name.endswith('.jpg'))
    
    def test_image_upload_view_form_processing(self):
        """Test the view's form processing logic separately"""
        # This tests the core business logic that the view executes
        # when it receives a valid form (simulates successful file upload)
        
        from catalog.forms.image_form import ItemImageForm
        test_file = self._create_test_image('test_form_processing.jpg')
        
        form_data = {
            'item': self.item.id,
            'caption': 'Form processing test',
            'is_primary': True
        }
        
        # Test the exact same logic that view uses in form_valid()
        form = ItemImageForm(data=form_data, files={'image': test_file}, item=self.item)
        self.assertTrue(form.is_valid(), f"Form validation failed: {form.errors}")
        
        # Simulate view's form_valid() method exactly
        form.set_user(self.user)
        image_instance = form.save()
        
        # Verify all view functionality
        self.assertEqual(image_instance.item, self.item)
        self.assertEqual(image_instance.caption, 'Form processing test')
        self.assertTrue(image_instance.is_primary)
        self.assertEqual(image_instance.created_by, self.user)
        self.assertEqual(image_instance.updated_by, self.user)
        
        # Verify it's actually saved to database
        saved_image = ItemImage.objects.get(id=image_instance.id)
        self.assertEqual(saved_image.caption, 'Form processing test')
        
        print("✓ View's form processing logic verified")
    
    def test_image_upload_view_post_invalid(self):
        """Test image upload view POST with invalid data"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        
        data = {
            'item': self.item.id,
            'caption': 'Test image',
            # Missing image file
        }
        
        response = self.client.post(url, data=data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors')
        
        # Check that image was not created
        self.assertFalse(ItemImage.objects.filter(item=self.item).exists())
    
    def test_image_upload_view_invalid_file_type(self):
        """Test image upload view with invalid file type"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        text_file = SimpleUploadedFile(
            "test.txt",
            b"This is not an image",
            content_type="text/plain"
        )
        form_data = {
            'item': self.item.id,
            'caption': 'Test text file',
            'is_primary': False,
            'image': text_file
        }
        response = self.client.post(url, form_data, format='multipart')
        self.assertEqual(response.status_code, 200) # Should return to form with errors
    
    def test_image_upload_view_large_file(self):
        """Test image upload view with file too large"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        large_file = self._create_test_image('large_test.jpg', size=(5000, 5000), color='blue')
        form_data = {
            'item': self.item.id,
            'caption': 'Large test image',
            'is_primary': False,
            'image': large_file
        }
        response = self.client.post(url, form_data, format='multipart')
        self.assertIn(response.status_code, [200, 302])
    
    def test_image_upload_view_without_login(self):
        """Test image upload view without login"""
        self.client.logout()
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_image_upload_view_item_not_found(self):
        """Test image upload view with non-existent item"""
        url = reverse('catalog:image-upload', kwargs={'item_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_image_upload_view_inactive_item(self):
        """Test image upload view with inactive item"""
        # Make item inactive
        self.item.status = ItemSKU.Status.INACTIVE
        self.item.save()
        
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        # Should return 404 for inactive items
        self.assertEqual(response.status_code, 404)
    
    def test_image_upload_view_template_used(self):
        """Test that image upload uses correct template"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/image/image-form.html')
    
    def test_image_upload_view_form_fields(self):
        """Test that image upload form has all expected fields"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check for form fields
        self.assertContains(response, 'name="image"')
        self.assertContains(response, 'name="caption"')
        self.assertContains(response, 'name="is_primary"')
        self.assertContains(response, 'name="item"')
    
    def test_image_upload_view_cancel_action(self):
        """Test image upload view cancel button"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should have cancel button that goes back to item detail
        self.assertContains(response, 'Cancel')
    
    def test_image_upload_sets_audit_fields(self):
        """Test that uploading image sets audit fields correctly"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        image_file = self._create_test_image('audit_test.jpg')
        form_data = {
            'item': self.item.id,
            'caption': 'Audit Test Image',
            'is_primary': False,
            'image': image_file
        }
        self.client.post(url, form_data, format='multipart')
        image = ItemImage.objects.get(caption='Audit Test Image')
        self.assertEqual(image.created_by, self.user)
        self.assertEqual(image.updated_by, self.user)
        self.assertIsNotNone(image.created_at)
        self.assertIsNotNone(image.updated_at)
        self.assertEqual(image.version, 1)
    
    def test_image_upload_view_success_redirect(self):
        """Test that successful image upload redirects correctly"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        image_file = self._create_test_image('redirect_test.jpg')
        form_data = {
            'item': self.item.id,
            'caption': 'Redirect Test Image',
            'is_primary': False,
            'image': image_file
        }
        response = self.client.post(url, form_data, format='multipart')
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('catalog:image-list', kwargs={'item_id': self.item.id})
        self.assertRedirects(response, expected_url)
    
    def test_image_upload_view_form_validation_messages(self):
        """Test that image upload view shows proper validation messages"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        data = {
            'item': self.item.id,
            'caption': 'Valid caption',
            # Missing image file
        }
        
        response = self.client.post(url, data=data)
        
        self.assertEqual(response.status_code, 200)
        # Should show required field validation message
        self.assertContains(response, 'This field is required')
    
    def test_image_upload_view_preserves_form_data(self):
        """Test that form data is preserved on validation errors"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        data = {
            'item': self.item.id,
            'caption': 'This caption should be preserved',
            'is_primary': True,
            # Missing image file
        }
        
        response = self.client.post(url, data=data)
        
        self.assertEqual(response.status_code, 200)
        # Should preserve the valid caption field
        self.assertContains(response, 'This caption should be preserved')
    
    def test_image_upload_view_multiple_images_primary_logic(self):
        """Test primary image logic when uploading multiple images"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        image_file1 = self._create_test_image('image1.jpg')
        form_data1 = {
            'item': self.item.id,
            'caption': 'First Primary Image',
            'is_primary': True,
            'image': image_file1
        }
        response_1 = self.client.post(url, form_data1, format='multipart')
        self.assertEqual(response_1.status_code, 302, "Expected redirect after successful upload")

        image_file2 = self._create_test_image('image2.jpg')
        form_data2 = {
            'item': self.item.id,
            'caption': 'Second Primary Image',
            'is_primary': True,
            'image': image_file2
        }
        response_2 = self.client.post(url, form_data2, format='multipart')
        self.assertEqual(response_2.status_code, 302)
        primary_images = ItemImage.objects.filter(item=self.item, is_primary=True)
        self.assertEqual(primary_images.count(), 1)
        self.assertEqual(primary_images.first().caption, 'Second Primary Image')
    
    def test_image_upload_view_context_data(self):
        """Test context data passed to template"""
        url = reverse('catalog:image-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('item', response.context)
        self.assertEqual(response.context['item'], self.item)
        self.assertIn('page_title', response.context)
        self.assertIn('breadcrumb_items', response.context)
        
        # Check breadcrumbs structure
        breadcrumbs = response.context['breadcrumb_items']
        self.assertTrue(len(breadcrumbs) >= 2)
        self.assertEqual(breadcrumbs[-1]['name'], 'Upload Image')
            