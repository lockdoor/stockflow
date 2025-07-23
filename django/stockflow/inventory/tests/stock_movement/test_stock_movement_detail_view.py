from django.test import TestCase, Client
from django.contrib.auth.models import User
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
from inventory.forms.stock_movement_form import StockMovementForm
from django.urls import reverse

class StockMovementDetailViewTest(TestCase):
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
        self.url = reverse('inventory:stock-movement-detail', args=[self.movement.id])

    def test_detail_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_detail_success(self):
        self.client.login(username='tester', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('stock_movement', response.context)
        self.assertEqual(response.context['stock_movement'], self.movement)
        self.assertContains(response, str(self.movement.id))

    def test_detail_not_found(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-movement-detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
