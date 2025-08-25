from django.test import TestCase, client
from django.urls import reverse

from tests.factories.user import AdminFactory, UserFactory
from tests.factories.production import ProductionOrderFactory

class ProductionOrderListViewTests(TestCase):
    def setUp(self):
        self.client = client.Client()
        self.admin = AdminFactory(username='admin', password='password')
        self.user = UserFactory(username='user', password='password')
        self.url = reverse('production:production-order-list')
        self.client.login(username=self.admin.username, password='password')

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_view_requires_permission(self):
        self.client.logout()
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_view_return_template_and_pagination(self):
        # Create some production orders
        self.orders = ProductionOrderFactory.create_batch(7, created_by=self.admin, updated_by=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'production/orders/production-order-list.html')
        # Should show only 5 orders per page (see paginate_by=5)
        self.assertEqual(len(response.context['production_orders']), 5)
        # Check pagination controls
        self.assertContains(response, 'pagination')
        # Check that at least one order is in the list
        for order in self.orders[2:]:
            self.assertContains(response, f"#{order.id}")
        # Go to page 2
        response2 = self.client.get(self.url + '?page=2')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.context['production_orders']), 2)
        for order in self.orders[:2]:
            self.assertContains(response2, f"#{order.id}")
