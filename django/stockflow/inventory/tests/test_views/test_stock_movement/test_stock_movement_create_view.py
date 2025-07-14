from inventory.signals import warehouse_signals
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
from django.urls import reverse

class StockMovementCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main', address='123 Main St',
            note='Main warehouse for testing',
            created_by=self.user, 
            updated_by=self.user)
        # สร้าง permission ทั้งสองแบบ
        self.perm1 = Permission.objects.get(codename='add_stockmovement')
        self.perm2 = Permission.objects.get(codename=f'can_manage_warehouse_{self.warehouse.id}')
        self.create_url = reverse('inventory:stock-movement-create', args=[self.warehouse.id])

    def test_create_with_add_stockmovement_permission(self):
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,
            'reference_id': 1,
            'note': 'test',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(StockMovement.objects.filter(note='test').exists())

    def test_create_with_can_manage_warehouse_permission(self):
        self.user.user_permissions.add(self.perm2)
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,
            'reference_id': 2,
            'note': 'test2',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(StockMovement.objects.filter(note='test2').exists())

    def test_create_without_permission(self):
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': 'INTERNAL',
            'reference_id': 3,
            'note': 'no permission',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(StockMovement.objects.filter(note='no permission').exists())
