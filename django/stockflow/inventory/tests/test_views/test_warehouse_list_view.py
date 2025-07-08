from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse

class WarehouseListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        for i in range(5):
            Warehouse.objects.create(
                name=f'Warehouse {i}',
                address=f'Address {i}',
                note=f'Note {i}',
                is_active=True,
                created_by=self.user,
                updated_by=self.user
            )

    def test_redirect_if_not_logged_in(self):
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_list_view_status_code_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_uses_correct_template_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'inventory/warehouse/warehouse.html')

    def test_list_view_context_contains_warehouses_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        self.assertIn('warehouses', response.context)
        self.assertEqual(response.context['warehouses'].count(), 5)
        names = [w.name for w in response.context['warehouses']]
        for i in range(5):
            self.assertIn(f'Warehouse {i}', names)

    def test_list_view_pagination_logged_in(self):
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        self.assertFalse(response.context['is_paginated'])
        self.assertEqual(len(response.context['warehouses']), 5)
