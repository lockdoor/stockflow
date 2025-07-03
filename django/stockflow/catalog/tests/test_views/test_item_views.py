from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models.item import ItemSKU, ItemSKUType, ItemSKUStatus
from catalog.forms.item_form import ItemForm

class ItemViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        # Assign permissions to the user
        add_permission = Permission.objects.get(codename='add_itemsku')
        change_permission = Permission.objects.get(codename='change_itemsku')
        self.user.user_permissions.add(add_permission)
        self.user.user_permissions.add(change_permission)
        
        ItemSKU.objects.create(
            sku_code='TEST001',
            name='Test Item 1',
            unit='pcs',
            type=ItemSKUType.PRODUCT,
            status=ItemSKUStatus.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.data = {
            "sku_code": 'TEST002',
            "name": 'Test Item 2',
            "unit": 'pcs',
            "type": ItemSKUType.PRODUCT,
            "status": ItemSKUStatus.ACTIVE,
            "created_by": self.user,
            "updated_by": self.user
        }
    
    # List View Tests
    def test_item_list_view_required_login(self):
        self.client.logout() # Ensure the user is logged out
        response = self.client.get(reverse('catalog:item-list'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login page

    def test_item_list_view(self):
        response = self.client.get(reverse('catalog:item-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item/item.html')
        self.assertContains(response, 'Items')
    
    # Create View Tests
    def test_item_create_view_required_login(self):
        self.client.logout() # Ensure the user is logged out
        response = self.client.get(reverse('catalog:item-create'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login page
    
    def test_item_create_view_required_permission(self):
        self.user.user_permissions.clear()  # Remove permissions
        response = self.client.get(reverse('catalog:item-create'))
        self.assertEqual(response.status_code, 403)  # Should return forbidden status

    def test_item_create_view(self):
        response = self.client.get(reverse('catalog:item-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item/partials/item-form.html')
        
    def test_item_create_view_post(self):
        response = self.client.post(reverse('catalog:item-create'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ItemSKU.objects.filter(sku_code='TEST002').exists())
        
    # Update View Tests
    def test_item_update_view_required_login(self):
        self.client.logout() # Ensure the user is logged out
        item = ItemSKU.objects.first()
        response = self.client.get(reverse('catalog:item-edit', kwargs={'pk': item.pk}))
        self.assertEqual(response.status_code, 302)  # Should redirect to login page

    def test_item_update_view_required_permission(self):
        self.user.user_permissions.clear()  # Remove permissions
        item = ItemSKU.objects.first()
        response = self.client.get(reverse('catalog:item-edit', kwargs={'pk': item.pk}))
        self.assertEqual(response.status_code, 403)  # Should return forbidden status
    
    def test_item_update_view(self):
        item = ItemSKU.objects.first()
        response = self.client.get(reverse('catalog:item-edit', kwargs={'pk': item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item/partials/item-form.html')
        self.assertContains(response, item.sku_code)
        
    def test_item_update_view_post(self):
        item = ItemSKU.objects.first()
        update_data = {
            'sku_code': item.sku_code,
            'name': "Updated Test Item",
            'unit': item.unit,
            'type': item.type,
            'status': item.status
        }
        response = self.client.post(reverse('catalog:item-edit', kwargs={'pk': item.pk}), update_data)
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.sku_code, 'TEST001')
        self.assertEqual(item.name, 'Updated Test Item')
        
    # Detail View Tests    
    def test_item_detail_view_required_login(self):
        self.client.logout() # Ensure the user is logged out
        item = ItemSKU.objects.first()
        response = self.client.get(reverse('catalog:item-detail', kwargs={'pk': item.pk}))
        self.assertEqual(response.status_code, 302)  # Should redirect to login page
