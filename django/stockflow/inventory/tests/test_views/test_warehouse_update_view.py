from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from inventory.models.warehouse import Warehouse

class WarehouseUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.user_with_perm = User.objects.create_user(username='permitted', password='testpass')
        perm = Permission.objects.get(codename='change_warehouse')
        self.user_with_perm.user_permissions.add(perm)
        self.warehouse = Warehouse.objects.create(
            name='Old Warehouse',
            address='Old Address',
            note='Old Note',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_redirect_if_not_logged_in(self):
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_forbidden_if_logged_in_without_permission(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_update_warehouse_success_with_permission(self):
        self.client.login(username='permitted', password='testpass')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {
            'name': 'Updated Warehouse',
            'address': 'Updated Address',
            'note': 'Updated Note',
            'is_active': False,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.warehouse.refresh_from_db()
        self.assertEqual(self.warehouse.name, 'Updated Warehouse')
        self.assertIn('warehouse-row.html', response.templates[0].name)

    def test_update_warehouse_invalid_with_permission(self):
        self.client.login(username='permitted', password='testpass')
        url = reverse('inventory:warehouse-edit', args=[self.warehouse.pk])
        data = {'name': '', 'address': '', 'note': '', 'is_active': True}
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('warehouse-form.html', response.templates[0].name)
        self.assertContains(response, 'name')
