from inventory.signals import warehouse_signals
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse

from django.urls import reverse

class StockMovementDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main', address='123 Main St',
            note='Main warehouse for testing',
            created_by=self.user, 
            updated_by=self.user)
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
        # Create dynamic permission and assign to user
        perm_codename = f'can_manage_warehouse_{self.warehouse.id}'
        
        # get permission by codename
        permission = Permission.objects.get(codename=perm_codename)
        self.user.user_permissions.add(permission)
        self.user.save()
        
    def test_found_can_manage_warehouse_permission(self):
        perm_codename = f'can_manage_warehouse_{self.warehouse.id}'
        permission = Permission.objects.get(codename=perm_codename)
        self.assertIsNotNone(permission)
        self.assertEqual(permission.codename, perm_codename)

    def test_delete_draft_with_permission(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_without_permission(self):
        self.user.user_permissions.clear()
        self.client.login(username='testuser', password='testpass')
        response = self.client.delete(f'/inventory/stockmovement/{self.draft_movement.pk}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_confirmed_should_fail(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.delete(f'/inventory/stockmovement/{self.confirmed_movement.pk}/delete/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(StockMovement.objects.filter(pk=self.confirmed_movement.pk).exists())

    def test_delete_not_found(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.delete(f'/inventory/stockmovement/99999/delete/')
        self.assertEqual(response.status_code, 404)
