from django.test import TestCase, client
from django.urls import reverse

from tests.factories.user import AdminFactory, UserFactory
from tests.factories.production import ProductionOrderFactory

class ProductionOrderDetailViewTests(TestCase):
    def setUp(self):
        self.client = client.Client()
        self.admin = AdminFactory(username='admin', password='password')
        self.user = UserFactory(username='user', password='password')
        self.production_order = ProductionOrderFactory(created_by=self.admin, updated_by=self.admin)
        self.url = reverse('production:production-order-detail', args=[self.production_order.id])
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

    def test_get_view_return_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'production/orders/production-order-detail.html')
        self.assertContains(response, f"Production Order #{self.production_order.id}")
        self.assertContains(response, self.production_order.warehouse.name)
        self.assertContains(response, self.production_order.get_status_display())
