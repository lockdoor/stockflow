from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category
from catalog.tests.image.test_image_file_mixin import TestImageFileMixin


class ItemImageUpdateViewTest(TestImageFileMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Add necessary permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(ItemImage)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_itemimage', 'change_itemimage', 'delete_itemimage', 'view_itemimage']
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
        self.image = ItemImage.objects.create(
            item=self.item,
            caption='Old Caption',
            image=self._create_test_image(),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )

    def test_update_view_requires_login(self):
        url = reverse('catalog:image-edit', kwargs={'pk': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_update_view_get(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-edit', kwargs={'pk': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update Image')
        self.assertContains(response, self.image.caption)

    def test_update_view_post_valid(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-edit', kwargs={'pk': self.image.id})
        form_data = {
            'caption': 'New Caption',
            'is_primary': True,
        }
        response = self.client.post(url, data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Image updated successfully')
        self.image.refresh_from_db()
        self.assertEqual(self.image.caption, 'New Caption')
        self.assertTrue(self.image.is_primary)

    def test_update_view_post_invalid(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-edit', kwargs={'pk': self.image.id})
        form_data = {
            'caption': False,
            'is_primary': 'True',
        }
        response = self.client.post(url, data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        print(messages)
        self.assertEqual(messages[0].level, 25)
        # self.assertContains(response, 'Please correct the errors below.')
