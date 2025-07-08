from django.test import TestCase
from django.contrib.auth.models import User
# from inventory.models.warehouse import Warehouse
from inventory.forms.warehouse_form import WarehouseForm

class WarehouseFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')

    def test_valid_form(self):
        data = {
            'name': 'Test Warehouse',
            'address': '123 Test Ave',
            'note': 'Test note',
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertTrue(form.is_valid())
        warehouse = form.save(commit=False)
        warehouse.created_by = self.user
        warehouse.updated_by = self.user
        warehouse.save()
        self.assertEqual(warehouse.name, 'Test Warehouse')
        self.assertTrue(warehouse.is_active)

    def test_invalid_form_missing_name(self):
        data = {
            'address': 'No name',
            'note': '',
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
