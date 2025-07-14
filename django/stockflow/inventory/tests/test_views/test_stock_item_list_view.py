from django.test import TestCase, Client
from django.contrib.auth.models import User
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from catalog.models.item import ItemSKU
from django.urls import reverse

class StockItemListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main', address='123', note='test', created_by=self.user, updated_by=self.user
        )
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        self.item1 = ItemSKU.objects.create(name='Item1', sku_code='SKU1', unit='pcs', created_by=self.user, updated_by=self.user)
        self.item2 = ItemSKU.objects.create(name='Item2', sku_code='SKU2', unit='pcs', created_by=self.user, updated_by=self.user)
        StockMovementItem.objects.create(
            stock_movement=self.movement,
            item=self.item1,
            movement_type=StockMovementItem.MovementType.IN_,
            quantity=5
        )
        StockMovementItem.objects.create(
            stock_movement=self.movement,
            item=self.item2,
            movement_type=StockMovementItem.MovementType.OUT,
            quantity=2
        )
        self.url = reverse('inventory:stock-item-movement-list', args=[self.movement.id])

    def test_list_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_list_view_success(self):
        self.client.login(username='tester', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, 'Item1')
        # self.assertContains(response, 'Item2')
        self.assertIn('movement_items', response.context)
        self.assertEqual(len(response.context['movement_items']), 2)

    def test_list_view_invalid_stock_movement_id(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-item-movement-list', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
