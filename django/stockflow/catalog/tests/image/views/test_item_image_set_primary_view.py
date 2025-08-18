from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category
from catalog.tests.image.test_image_file_mixin import TestImageFileMixin

class ItemImageSetPrimaryViewTest(TestImageFileMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Add permission to set primary (change_itemimage)
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(ItemImage)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['change_itemimage', 'view_itemimage']
        )
        self.user.user_permissions.set(permissions)
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
            image=self._create_test_image('img1.jpg'),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        self.image2 = ItemImage.objects.create(
            item=self.item,
            caption='Image 2',
            image=self._create_test_image('img2.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_set_primary_requires_login(self):
        url = reverse('catalog:image-set-primary', kwargs={'pk': self.image1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_set_primary_no_permission(self):
        user2 = User.objects.create_user(username='noperm', password='nopass123')
        self.client.login(username='noperm', password='nopass123')
        url = reverse('catalog:image-set-primary', kwargs={'pk': self.image1.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])

    def test_set_primary_success(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-set-primary', kwargs={'pk': self.image1.id})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Image set as primary successfully')
        self.image1.refresh_from_db()
        self.image2.refresh_from_db()
        self.assertTrue(self.image1.is_primary)
        self.assertFalse(self.image2.is_primary)
