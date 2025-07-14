from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from inventory.models.warehouse import Warehouse

class WarehouseCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.user_with_perm = User.objects.create_user(username='permitted', password='testpass')
        perm = Permission.objects.get(codename='add_warehouse')
        self.user_with_perm.user_permissions.add(perm)

    def test_redirect_if_not_logged_in(self):
        url = reverse('inventory:warehouse-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_forbidden_if_logged_in_without_permission(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_create_warehouse_success_with_permission(self):
        self.client.login(username='permitted', password='testpass')
        url = reverse('inventory:warehouse-create')
        data = {
            'name': 'Permitted Warehouse',
            'address': 'Permitted Address',
            'note': 'Permitted Note',
            'is_active': True,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Warehouse.objects.filter(name='Permitted Warehouse').exists())
        self.assertIn('warehouse-row.html', response.templates[0].name)

    def test_create_warehouse_invalid_with_permission(self):
        self.client.login(username='permitted', password='testpass')
        url = reverse('inventory:warehouse-create')
        data = {'address': 'No name', 'note': '', 'is_active': True}
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('warehouse-form.html', response.templates[0].name)
        self.assertContains(response, 'name')
