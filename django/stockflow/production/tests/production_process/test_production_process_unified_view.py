from django.test import TestCase, client
from django.urls import reverse

from tests.mixin import MixinSetupProduction
from tests.factories.user import UserFactory


class ProductionProcessUnifiedViewTests(MixinSetupProduction, TestCase):
    def setUp(self):
        super().setUp()
        self.product_order = self.production_orders[0]
        self.client = client.Client()
        self.url = reverse('production:production-process-unified-create', args=[1])  # Assuming production_order_id=1
        self.user = UserFactory(username='testuser', password='password')

    def test_shoud_has_production_order(self):
        self.assertTrue(len(self.production_orders) > 0)
    
    def test_view_must_log_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        
    def test_view_must_have_permission(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)