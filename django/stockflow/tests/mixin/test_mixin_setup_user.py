from django.test import TestCase
from ..factories.user import AdminFactory

class MixinSetupUser:
    def setUp(self):
        super().setUp()
        self.admin_user = AdminFactory.create(username='admin', password='admin123')

class MyUserTests(MixinSetupUser, TestCase):
    def test_admin_user(self):
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
