"""
ItemImageBulkUploadView Tests

Tests for ItemImageBulkUploadView (bulk image upload).
Covers form validation, multiple file upload, permissions, and authentication.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from catalog.tests.image.test_image_file_mixin import TestImageFileMixin
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category

class ItemImageBulkUploadViewTest(TestImageFileMixin, TestCase):
    """Test cases for ItemImageBulkUploadView"""
    
    def setUp(self):
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
        content_type = ContentType.objects.get_for_model(ItemImage)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_itemimage', 'change_itemimage', 'delete_itemimage', 'view_itemimage']
        )
        self.user.user_permissions.set(permissions)
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
            status=ItemSKU.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        self.client.login(username='testuser', password='testpass123')

    def test_bulk_upload_view_get_no_perm(self):
        self.client.logout()
        self.client.login(username='testuser_no_perm', password='testpass123')
        url = reverse('catalog:image-bulk-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_bulk_upload_view_get(self):
        url = reverse('catalog:image-bulk-upload', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bulk Upload Images')
        self.assertContains(response, 'name="images"')
        self.assertContains(response, 'name="set_first_as_primary"')

    def test_bulk_upload_view_post_valid(self):
        url = reverse('catalog:image-bulk-upload', kwargs={'item_id': self.item.id})
        img1 = self._create_test_image('bulk1.jpg', color='blue')
        img2 = self._create_test_image('bulk2.jpg', color='green')
        form_data = {
            'item': self.item.id,
            'set_first_as_primary': True,
        }
        files = [img1, img2]
        response = self.client.post(url, data={**form_data, 'images': files}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Successfully uploaded')
        self.assertEqual(ItemImage.objects.filter(item=self.item).count(), 2)
        self.assertTrue(ItemImage.objects.filter(item=self.item, is_primary=True).exists())

    def test_bulk_upload_view_post_no_files(self):
        url = reverse('catalog:image-bulk-upload', kwargs={'item_id': self.item.id})
        form_data = {
            'item': self.item.id,
            'set_first_as_primary': True,
        }
        response = self.client.post(url, data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        # print(messages[0].level)
        self.assertEqual(messages[0].level, 40)
        # self.assertContains(response, 'Please select at least one image file.')
        self.assertEqual(ItemImage.objects.filter(item=self.item).count(), 0)
