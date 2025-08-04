# catalog/tests/item/test_item_list_view.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class ItemListViewTest(TestCase):
    """Test cases for ItemListView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test items
        self.item1 = ItemSKU.objects.create(
            sku_code='TEST001',
            name='Test Item 1',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            sku_code='TEST002',
            name='Test Item 2',
            unit='kg',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT for PRODUCT type
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('catalog:item-list')

    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_view_with_authenticated_user(self):
        """Test view access with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Item 1')
        self.assertContains(response, 'Test Item 2')

    def test_context_object_name(self):
        """Test that context contains 'items'"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertIn('items', response.context)
        self.assertEqual(len(response.context['items']), 2)

    def test_template_used(self):
        """Test correct template is used"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertTemplateUsed(response, 'catalog/item/item-list.html')

    def test_ordering_by_created_at_desc(self):
        """Test items are ordered by created_at descending"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        items = response.context['items']
        # item2 was created after item1, so should appear first
        self.assertEqual(items[0], self.item2)
        self.assertEqual(items[1], self.item1)

    def test_empty_item_list(self):
        """Test view with no items"""
        ItemSKU.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 0)

    def test_inactive_items_shown(self):
        """Test that inactive items are also shown in the list"""
        # Create an inactive item - use PACKAGE type to avoid business rule issues
        inactive_item = ItemSKU.objects.create(
            sku_code='INACTIVE001',
            name='Inactive Item',
            unit='pcs',
            type=ItemSKU.Type.PACKAGE,  # Use PACKAGE type
            status=ItemSKU.Status.DRAFT,  # Start as DRAFT then change to INACTIVE
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Change to inactive after creation to bypass business rules
        inactive_item.status = ItemSKU.Status.INACTIVE
        inactive_item.save(update_fields=['status'])
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inactive Item')
        self.assertEqual(len(response.context['items']), 3)

    def test_view_performance_with_many_items(self):
        """Test view performance with many items"""
        # Create many items
        items = []
        for i in range(100):
            items.append(ItemSKU(
                sku_code=f'BULK{i:03d}',
                name=f'Bulk Item {i}',
                unit='pcs',
                type=ItemSKU.Type.RAW,
                category=self.category,
                created_by=self.user,
                updated_by=self.user
            ))
        ItemSKU.objects.bulk_create(items)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Should have 102 items total (2 original + 100 bulk created)
        self.assertEqual(len(response.context['items']), 102)
