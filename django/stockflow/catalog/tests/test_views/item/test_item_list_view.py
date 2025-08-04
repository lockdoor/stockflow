from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class ItemListViewTest(TestCase):
    """
    Test case for the ItemListView
    """

    def setUp(self):
        """
        Set up test environment
        """
        # Create a test user with necessary permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create another user for testing
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword2'
        )
        
        # Note: ListView typically doesn't need specific permissions beyond login
        # It inherits LoginRequiredMixin but not PermissionRequiredMixin
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create test items
        self.raw_item = ItemSKU.objects.create(
            sku_code='RAW-001',
            name='Raw Material Item',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.product_item = ItemSKU.objects.create(
            sku_code='PROD-001',
            name='Product Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.package_item = ItemSKU.objects.create(
            sku_code='PKG-001',
            name='Package Item',
            unit='pcs',
            type=ItemSKU.Type.PACKAGE,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Initialize the test client
        self.client = Client()
        
        # URL for item list view
        self.item_list_url = reverse('catalog:item-list')

    def test_view_requires_login(self):
        """
        Test that view requires authentication
        """
        # Access without login should redirect to login page
        response = self.client.get(self.item_list_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login page
        self.assertTrue(response.url.startswith('/login/'))
        
    def test_view_with_login(self):
        """
        Test view when user is logged in
        """
        # Login the user
        self.client.login(username='testuser', password='testpassword')
        
        # Access the view
        response = self.client.get(self.item_list_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check if all items are in the context
        self.assertIn('items', response.context)
        items = list(response.context['items'])
        self.assertEqual(len(items), 3)
        
        # Check if items are sorted by created_at in descending order (newest first)
        self.assertEqual(items[0].sku_code, self.package_item.sku_code)
        self.assertEqual(items[1].sku_code, self.product_item.sku_code)
        self.assertEqual(items[2].sku_code, self.raw_item.sku_code)

    def test_view_html_content(self):
        """
        Test the HTML content of the view
        """
        # Login the user
        self.client.login(username='testuser', password='testpassword')
        
        # Access the view
        response = self.client.get(self.item_list_url)
        
        # Check response contains expected HTML elements
        content = response.content.decode('utf-8')
        
        # Check table headers
        self.assertIn('<th>SKU</th>', content)
        self.assertIn('<th>Name</th>', content)
        self.assertIn('<th>Type</th>', content)
        self.assertIn('<th>Status</th>', content)
        self.assertIn('<th>Category</th>', content)
        
        # Check if items are in the response
        self.assertIn('RAW-001', content)
        self.assertIn('PROD-001', content)
        self.assertIn('PKG-001', content)
        self.assertIn('Raw Material Item', content)
        self.assertIn('Product Item', content)
        self.assertIn('Package Item', content)
        
    def test_empty_item_list(self):
        """
        Test when no items exist
        """
        # Delete all items
        ItemSKU.objects.all().delete()
        
        # Login the user
        self.client.login(username='testuser', password='testpassword')
        
        # Access the view
        response = self.client.get(self.item_list_url)
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check if items list is empty
        self.assertIn('items', response.context)
        items = list(response.context['items'])
        self.assertEqual(len(items), 0)
        
        # Check if "No items found" message is displayed
        content = response.content.decode('utf-8')
        self.assertIn('No items found', content)

    def test_view_with_htmx_request(self):
        """
        Test the view responds properly to HTMX requests
        """
        # Login the user
        self.client.login(username='testuser', password='testpassword')
        
        # Simulate an HTMX request
        response = self.client.get(
            self.item_list_url,
            HTTP_HX_REQUEST='true'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # The response should only include the content, not the full page
        content = response.content.decode('utf-8')
        self.assertIn('RAW-001', content)
        self.assertNotIn('<html>', content)  # Should not include full HTML document

    def test_ordering_is_applied(self):
        """
        Test that the ordering is correctly applied to the queryset
        """
        # Create a new item with a later created_at time
        new_item = ItemSKU.objects.create(
            sku_code='NEW-001',
            name='New Test Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Login the user
        self.client.login(username='testuser', password='testpassword')
        
        # Access the view
        response = self.client.get(self.item_list_url)
        
        # Get items from context
        items = list(response.context['items'])
        
        # The new item should be first in the list (most recently created)
        self.assertEqual(items[0].sku_code, new_item.sku_code)
