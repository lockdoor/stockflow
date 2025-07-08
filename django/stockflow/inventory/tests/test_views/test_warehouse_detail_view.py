from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse

class WarehouseDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Detail Warehouse',
            address='123 Detail St',
            note='Detail note',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_redirect_if_not_logged_in(self):
        url = reverse('inventory:warehouse-detail', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_detail_view_status_code_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-detail', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_view_uses_correct_template_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-detail', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'inventory/warehouse/warehouse-detail.html')

    def test_detail_view_context_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-detail', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertIn('warehouse', response.context)
        self.assertEqual(response.context['warehouse'], self.warehouse)
