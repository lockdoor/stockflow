from django.test import TestCase
from django.contrib.auth.models import User, Permission
from catalog.forms.create_raw_item_form import CreateRawItemForm

#models
from catalog.models.category import Category
from catalog.models.item import ItemSKU

class ItemsViewTest(TestCase):
    def setUp(self):
        self.URL = '/catalog/items'
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')
        self.permission = Permission.objects.get(codename='add_itemsku')
        self.permission_category = Permission.objects.get(codename='add_category')
        self.category = Category.objects.create(
            name='Test Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_items_view_requires_login(self):
        """
        Test that the create raw item view requires login.
        """
        self.client.logout()  # Ensure the user is logged out
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)

    def test_items_view(self):
        """
        Test that the items view returns a 200 status code.
        """
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/items.html')
        self.assertEqual(response.request['PATH_INFO'], self.URL)
    
    def test_items_should_has_zero_items(self):
        """
        Test that the items view should have zero items.
        """
        response = self.client.get(self.URL)
        self.assertQuerySetEqual(response.context['items'], [])

    def test_items_should_has_one_category(self):
        item = ItemSKU.objects.create(
            sku_code='TEST123',
            name='Test Item',
            unit='pcs',
            status='available',
            description='This is a test item.',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )

        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertContains(response, item.name)
        self.assertQuerySetEqual(response.context['items'], [item])

    def test_items_should_has_two_item(self):
        item_1 = ItemSKU.objects.create(
            sku_code='TEST123',
            name='Test Item 1',
            unit='pcs',
            status='available',
            description='This is a test item 1.',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        item_2 = ItemSKU.objects.create(
            sku_code='TEST456',
            name='Test Item 2',
            unit='pcs',
            status='available',
            description='This is a test item 2.',
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )

        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertContains(response, item_1.name)
        self.assertContains(response, item_2.name)
        # check response context categories has two categories
        self.assertEqual(len(response.context['items']), 2)

    def test_items_view_has_link_to_create_item(self):
        """
        Test that the items view has a link to create a new item.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertContains(response, 'href="/catalog/create_raw_item?next=/catalog/items"')