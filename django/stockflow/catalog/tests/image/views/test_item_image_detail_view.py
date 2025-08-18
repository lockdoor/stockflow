
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category
from catalog.tests.image.test_image_file_mixin import TestImageFileMixin

class ItemImageDetailViewTest(TestImageFileMixin, TestCase):
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
        self.image = ItemImage.objects.create(
            item=self.item,
            caption='Image 1',
            image=self._create_test_image(),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_detail_view_requires_login(self):
        url = reverse('catalog:image-detail', kwargs={'pk': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_detail_view_success(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-detail', kwargs={'pk': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.caption)
        self.assertContains(response, self.item.name)
        self.assertContains(response, 'Image')
