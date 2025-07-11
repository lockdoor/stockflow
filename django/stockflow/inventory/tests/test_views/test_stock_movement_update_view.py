from inventory.signals import warehouse_signals
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
from django.urls import reverse

class StockMovementUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main', address='123 Main St',
            note='Main warehouse for testing',
            created_by=self.user, 
            updated_by=self.user)
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            reference_type=StockMovement.ReferenceType.NONE,
            reference_id=1,
            note='original',
            created_by=self.user,
            updated_by=self.user
        )
        self.update_url = reverse('inventory:stock-movement-edit', args=[self.movement.id])
        # สร้าง permission ทั้งสองแบบ
        self.perm1 = Permission.objects.get(codename='change_stockmovement')
        self.perm2 = Permission.objects.get(codename=f'can_manage_warehouse_{self.warehouse.id}')
       
    def test_update_with_change_stockmovement_permission(self):
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,
            'reference_id': 99,
            'note': 'updated1',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, 'updated1')
        self.assertEqual(self.movement.reference_id, 99)

    def test_update_with_can_manage_warehouse_permission(self):
        self.user.user_permissions.add(self.perm2)
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'reference_id': 100,
            'note': 'updated2',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, 'updated2')
        self.assertEqual(self.movement.reference_id, 100)

    def test_update_without_permission(self):
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.ADJUST,
            'reference_id': 101,
            'note': 'should not update',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 403)
        self.movement.refresh_from_db()
        self.assertNotEqual(self.movement.note, 'should not update')
