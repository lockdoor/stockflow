from inventory.signals import warehouse_signals
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse

from django.urls import reverse

class StockMovementDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse', 
            code='MAIN01',
            address='123 Main St',
            note='Main warehouse for testing',
            is_active=True,
            created_by=self.user, 
            updated_by=self.user
        )
        self.confirmed_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.CONFIRMED,
            created_by=self.user,
            updated_by=self.user
        )
        self.draft_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Setup permissions
        self.delete_permission = Permission.objects.get(codename='delete_stockmovement')
        
        # Get warehouse-specific permission (created by signal)
        self.warehouse_permission = Permission.objects.get(
            codename=f'can_manage_warehouse_{self.warehouse.id}'
        )
        
    def test_found_can_manage_warehouse_permission(self):
        """Test that warehouse-specific permission exists"""
        perm_codename = f'can_manage_warehouse_{self.warehouse.id}'
        permission = Permission.objects.get(codename=perm_codename)
        self.assertIsNotNone(permission)
        self.assertEqual(permission.codename, perm_codename)

    def test_delete_draft_with_global_permission(self):
        """Test deletion with global delete permission"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_draft_with_warehouse_permission(self):
        """Test deletion with warehouse-specific permission"""
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_without_permission(self):
        """Test deletion fails without proper permissions"""
        # No permissions granted
        self.client.login(username='testuser', password='testpass')
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_confirmed_should_fail(self):
        """Test that confirmed movements cannot be deleted"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(f'/inventory/stockmovement/{self.confirmed_movement.pk}/delete/')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot delete confirmed movement", response.content.decode())
        self.assertTrue(StockMovement.objects.filter(pk=self.confirmed_movement.pk).exists())

    def test_delete_not_found(self):
        """Test deletion of non-existent stock movement"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(f'/inventory/stockmovement/99999/delete/')
        self.assertEqual(response.status_code, 404)

    def test_delete_requires_login(self):
        """Test that deletion requires authentication"""
        # Not logged in
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_different_warehouse_permission_denied(self):
        """Test that warehouse-specific permission only works for that warehouse"""
        # Create another warehouse and stock movement
        other_warehouse = Warehouse.objects.create(
            name='Other Warehouse',
            code='OTHER01',
            address='456 Other St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        other_movement = StockMovement.objects.create(
            warehouse=other_warehouse,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Give user permission only for the first warehouse
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Should fail to delete movement from other warehouse
        response = self.client.delete(f'/inventory/stockmovement/{other_movement.pk}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(StockMovement.objects.filter(pk=other_movement.pk).exists())

    def test_delete_response_headers(self):
        """Test that deletion response includes proper HTMX headers"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'stockMovementDeleted')
