from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.tests.image.test_image_file_mixin import TestImageFileMixin
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category

class ItemImageListViewTest(TestImageFileMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            note='Test note',
            created_by=self.user,
            updated_by=self.user
        )
        self.item = ItemSKU.objects.create(
            name='Test Item',
            sku_code='SKU123',
            unit='pcs',
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        self.image1 = ItemImage.objects.create(
            item=self.item,
            caption='Image 1',
            image=self._create_test_image(),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.image2 = ItemImage.objects.create(
            item=self.item,
            caption='Image 2',
            image=self._create_test_image(),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
    def test_list_view_requires_login(self):
        url = reverse('catalog:image-list', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_list_view_success(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-list', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item.name)
        self.assertContains(response, 'Images')
        self.assertContains(response, self.image1.caption)
        self.assertContains(response, self.image2.caption)

    def test_list_view_context_images(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-list', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        images = response.context['images']
        self.assertEqual(len(images), 2)
        self.assertIn(self.image1, images)
        self.assertIn(self.image2, images)
