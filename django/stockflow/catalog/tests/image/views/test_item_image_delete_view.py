from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category
from catalog.tests.image.test_image_file_mixin import TestImageFileMixin

class ItemImageDeleteViewTest(TestImageFileMixin, TestCase):

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
            caption='To be deleted',
            image=self._create_test_image(),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
    def test_delete_view_no_permission(self):
        # สร้าง user ที่ไม่มี permission
        user2 = User.objects.create_user(username='noperm', password='nopass123')
        self.client.login(username='noperm', password='nopass123')
        url = reverse('catalog:image-delete', kwargs={'pk': self.image.id})
        # GET
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])
        # POST
        response = self.client.post(url, data={'next': ''})
        self.assertIn(response.status_code, [302, 403])

    def test_delete_view_requires_login(self):
        url = reverse('catalog:image-delete', kwargs={'pk': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_delete_view_get(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-delete', kwargs={'pk': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Image')
        self.assertContains(response, self.image.caption)

    def test_delete_view_post(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('catalog:image-delete', kwargs={'pk': self.image.id})
        response = self.client.post(url, data={'next': ''}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Image deleted successfully')
        self.assertFalse(ItemImage.objects.filter(pk=self.image.id).exists())
