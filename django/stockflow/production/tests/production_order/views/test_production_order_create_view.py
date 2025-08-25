from django.test import TestCase, client
from django.urls import reverse

from tests.factories.user import AdminFactory, UserFactory


class ProductionOrderCreateViewTests(TestCase):
    def setUp(self):
        self.client = client.Client()
        self.url = reverse('production:production-order-create')
        self.admin = AdminFactory(username='admin', password='password')
        self.user = UserFactory(username='user', password='password')
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
        