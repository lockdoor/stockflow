from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement, StockMovementReferenceType, StockMovementStatus

class StockMovementByWareHouseListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse1 = Warehouse.objects.create(
            name='Warehouse 1',
            address='A',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.warehouse2 = Warehouse.objects.create(
            name='Warehouse 2',
            address='B',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        for i in range(3):
            StockMovement.objects.create(
                reference_type=StockMovementReferenceType.PACKING_LIST,
                warehouse=self.warehouse1,
                created_by=self.user,
                updated_by=self.user,
                status=StockMovementStatus.CONFIRMED
            )
        for i in range(2):
            StockMovement.objects.create(
                reference_type=StockMovementReferenceType.ADJUST,
                warehouse=self.warehouse2,
                created_by=self.user,
                updated_by=self.user,
                status=StockMovementStatus.CONFIRMED
            )

    def test_list_view_requires_login(self):
        url = reverse('inventory:stock-movement-list', args=[self.warehouse1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_list_view_for_warehouse1(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-movement-list', args=[self.warehouse1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/stock/partials/stock-movement-list.html')
        self.assertEqual(len(response.context['stock_movements']), 3)
        for movement in response.context['stock_movements']:
            self.assertEqual(movement.warehouse, self.warehouse1)

    def test_list_view_for_warehouse2(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-movement-list', args=[self.warehouse2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_movements']), 2)
        for movement in response.context['stock_movements']:
            self.assertEqual(movement.warehouse, self.warehouse2)
