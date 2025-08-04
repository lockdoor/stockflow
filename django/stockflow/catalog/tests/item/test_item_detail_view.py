from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.mixins.item_status import ItemStatusMixin

User = get_user_model()


class ItemDetailViewTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user with permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Add required permissions
        view_permission = Permission.objects.get(codename='view_itemsku')
        self.user.user_permissions.add(view_permission)
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item
        self.item = ItemSKU.objects.create(
            sku_code='DETAIL001',
            name='Detail Test Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemStatusMixin.Status.ACTIVE,
            category=self.category,
            note='This is a test item for detail view',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('catalog:item-detail', kwargs={'pk': self.item.pk})

    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_view_with_authenticated_user(self):
        """Test view access with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template_used(self):
        """Test correct template is used"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'catalog/item/item-detail.html')

    def test_context_object_name(self):
        """Test that context contains 'item'"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertIn('item', response.context)
        self.assertEqual(response.context['item'], self.item)

    def test_context_data(self):
        """Test that all necessary data is in context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check context variables
        self.assertIn('item', response.context)
        self.assertEqual(response.context['item'], self.item)

    def test_item_details_displayed(self):
        """Test that item details are displayed correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertContains(response, self.item.sku_code)
        self.assertContains(response, self.item.name)
        self.assertContains(response, 'RAW')  # Type badge display
        self.assertContains(response, 'ACTIVE')  # Status badge display
        self.assertContains(response, 'This is a test item for detail view')  # Note

    def test_item_with_no_category(self):
        """Test item detail view with no category"""
        item_no_cat = ItemSKU.objects.create(
            sku_code='NOCAT001',
            name='No Category Item',
            unit='pcs',
            type=ItemSKU.Type.PACKAGE,
            status=ItemStatusMixin.Status.DRAFT,  # Business rule: PACKAGE needs DRAFT
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:item-detail', kwargs={'pk': item_no_cat.pk})
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Category Item')

    def test_item_with_no_note(self):
        """Test item detail view with no note"""
        item_no_note = ItemSKU.objects.create(
            sku_code='NONOTE001',
            name='No Note Item',
            unit='pcs',
            type=ItemSKU.Type.PACKAGE,
            status=ItemStatusMixin.Status.DRAFT,  # Business rule: PACKAGE needs DRAFT
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:item-detail', kwargs={'pk': item_no_note.pk})
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Note Item')

    def test_inactive_item_detail(self):
        """Test detail view for inactive item"""
        # First create active, then update to inactive to bypass business rules
        inactive_item = ItemSKU.objects.create(
            sku_code='INACTIVE001',
            name='Inactive Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemStatusMixin.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update to inactive using update() to bypass validation
        ItemSKU.objects.filter(pk=inactive_item.pk).update(status=ItemStatusMixin.Status.INACTIVE)
        inactive_item.refresh_from_db()
        
        url = reverse('catalog:item-detail', kwargs={'pk': inactive_item.pk})
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inactive Item')
        self.assertContains(response, 'INACTIVE')

    def test_nonexistent_item(self):
        """Test detail view for non-existent item returns 404"""
        nonexistent_url = reverse('catalog:item-detail', kwargs={'pk': 99999})
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(nonexistent_url)
        
        self.assertEqual(response.status_code, 404)

    def test_audit_fields_display(self):
        """Test that audit fields are displayed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertContains(response, 'Created:')
        self.assertContains(response, 'Updated:')
        self.assertContains(response, 'testuser')
        
        # Check date format - try the actual format from template (Aug 04, 2025)
        self.assertContains(response, self.item.created_at.strftime('%b %d, %Y'))

    def test_item_type_display(self):
        """Test that item type is displayed correctly"""
        # Test RAW type (can be ACTIVE)
        raw_item = ItemSKU.objects.create(
            sku_code='RAW001',
            name='Raw Test',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemStatusMixin.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:item-detail', kwargs={'pk': raw_item.pk})
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'RAW')

        # Test PRODUCT type (needs DRAFT)
        product_item = ItemSKU.objects.create(
            sku_code='PRODUCT001',
            name='Product Test',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemStatusMixin.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:item-detail', kwargs={'pk': product_item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PRODUCT')

        # Test PACKAGE type (needs DRAFT)
        package_item = ItemSKU.objects.create(
            sku_code='PACKAGE001',
            name='Package Test',
            unit='pcs',
            type=ItemSKU.Type.PACKAGE,
            status=ItemStatusMixin.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:item-detail', kwargs={'pk': package_item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PACKAGE')

    def test_item_status_display(self):
        """Test that item status is displayed correctly"""
        # Test ACTIVE status
        active_item = ItemSKU.objects.create(
            sku_code='STATUSACTIVE001',
            name='Status Test ACTIVE',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemStatusMixin.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:item-detail', kwargs={'pk': active_item.pk})
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ACTIVE')
        
    def test_inactive_item_status_display(self):
        """Test inactive status display separately to handle business rules"""
        # Create active first, then update to inactive
        item = ItemSKU.objects.create(
            sku_code='STATUSINACTIVE001',
            name='Status Test INACTIVE',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemStatusMixin.Status.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update to inactive using update() to bypass validation
        ItemSKU.objects.filter(pk=item.pk).update(status=ItemStatusMixin.Status.INACTIVE)
        item.refresh_from_db()
        
        url = reverse('catalog:item-detail', kwargs={'pk': item.pk})
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INACTIVE')

    def test_category_link_if_exists(self):
        """Test that category link is displayed if category exists"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # The item has a category, so it should be displayed
        self.assertContains(response, self.category.name)
