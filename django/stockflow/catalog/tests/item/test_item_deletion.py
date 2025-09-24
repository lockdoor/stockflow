"""
Test cases for Item deletion functionality

Tests the can_be_deleted method and ItemDeleteView
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models import ItemSKU, Category, BOM
from inventory.models import StockMovementItem, StockMovement, Warehouse
from decimal import Decimal


class ItemDeletionTest(TestCase):
    """Test cases for item deletion functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user with permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Add permissions
        permissions = [
            'catalog.add_itemsku',
            'catalog.change_itemsku',
            'catalog.delete_itemsku',
            'catalog.view_itemsku',
        ]
        for perm_codename in permissions:
            permission = Permission.objects.get(codename=perm_codename.split('.')[1])
            self.user.user_permissions.add(permission)
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test items
        self.item1 = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item 1',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            sku_code='TEST-002',
            name='Test Item 2',
            unit='pcs', 
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT for PRODUCT type
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item3 = ItemSKU.objects.create(
            sku_code='TEST-003',
            name='Test Item 3',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client = Client()
        
    def test_can_be_deleted_no_references(self):
        """Test that item with no references can be deleted"""
        can_delete, blocking_refs = self.item1.can_be_deleted()
        self.assertTrue(can_delete)
        self.assertEqual(len(blocking_refs), 0)
        
    def test_can_be_deleted_with_bom_as_parent(self):
        """Test that item with BOM as parent cannot be deleted"""
        # Create BOM with item2 as parent
        BOM.objects.create(
            parent_sku=self.item2,
            component_sku=self.item1,
            quantity=Decimal('5.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        can_delete, blocking_refs = self.item2.can_be_deleted()
        self.assertFalse(can_delete)
        self.assertEqual(len(blocking_refs), 1)
        self.assertEqual(blocking_refs[0]['type'], 'BOM (as parent)')
        
    def test_can_be_deleted_with_bom_as_component(self):
        """Test that item used as BOM component cannot be deleted"""
        # Create BOM with item1 as component
        BOM.objects.create(
            parent_sku=self.item2,
            component_sku=self.item1,
            quantity=Decimal('3.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        can_delete, blocking_refs = self.item1.can_be_deleted()
        self.assertFalse(can_delete)
        self.assertEqual(len(blocking_refs), 1)
        self.assertEqual(blocking_refs[0]['type'], 'BOM (as component)')
        
    def test_item_detail_view_with_deletable_item(self):
        """Test item detail view shows delete button for deletable item"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('catalog:item-detail', kwargs={'pk': self.item1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['can_delete'])
        self.assertContains(response, 'Delete Item')
        self.assertContains(response, reverse('catalog:item-delete', kwargs={'pk': self.item1.pk}))
        
    def test_item_detail_view_with_non_deletable_item(self):
        """Test item detail view shows disabled delete button for non-deletable item"""
        # Create BOM to make item non-deletable
        BOM.objects.create(
            parent_sku=self.item2,
            component_sku=self.item1,
            quantity=Decimal('2.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('catalog:item-detail', kwargs={'pk': self.item1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['can_delete'])
        self.assertContains(response, 'disabled')
        self.assertContains(response, 'Cannot delete: Item is referenced by other records')
        
    def test_item_delete_confirm_page_deletable(self):
        """Test delete confirmation page for deletable item"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('catalog:item-delete', kwargs={'pk': self.item1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['can_delete'])
        self.assertContains(response, 'Confirm Deletion')
        self.assertContains(response, 'This item has no references and can be safely deleted')
        
    def test_item_delete_confirm_page_non_deletable(self):
        """Test delete confirmation page for non-deletable item"""
        # Create BOM to make item non-deletable
        BOM.objects.create(
            parent_sku=self.item2,
            component_sku=self.item1,
            quantity=Decimal('1.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('catalog:item-delete', kwargs={'pk': self.item1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['can_delete'])
        self.assertContains(response, 'Cannot Delete Item')
        self.assertContains(response, 'Deletion Blocked')
        self.assertContains(response, 'BOM (as component)')
        
    def test_successful_item_deletion(self):
        """Test successful item deletion"""
        self.client.login(username='testuser', password='testpass123')
        
        # Confirm item exists
        self.assertTrue(ItemSKU.objects.filter(pk=self.item1.pk).exists())
        
        url = reverse('catalog:item-delete', kwargs={'pk': self.item1.pk})
        response = self.client.post(url)
        
        # Should redirect to item list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('catalog:item-list'))
        
        # Item should be deleted
        self.assertFalse(ItemSKU.objects.filter(pk=self.item1.pk).exists())
        
    def test_blocked_item_deletion(self):
        """Test that non-deletable item cannot be deleted"""
        # Create BOM to make item non-deletable
        BOM.objects.create(
            parent_sku=self.item2,
            component_sku=self.item1,
            quantity=Decimal('1.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Confirm item exists
        self.assertTrue(ItemSKU.objects.filter(pk=self.item1.pk).exists())
        
        url = reverse('catalog:item-delete', kwargs={'pk': self.item1.pk})
        response = self.client.post(url)
        
        # Should redirect to item detail
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('catalog:item-detail', kwargs={'pk': self.item1.pk}))
        
        # Item should still exist
        self.assertTrue(ItemSKU.objects.filter(pk=self.item1.pk).exists())
        
    def test_permission_required_for_delete_view(self):
        """Test that delete permission is required"""
        # Remove delete permission
        permission = Permission.objects.get(codename='delete_itemsku')
        self.user.user_permissions.remove(permission)
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('catalog:item-delete', kwargs={'pk': self.item1.pk})
        response = self.client.get(url)
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)