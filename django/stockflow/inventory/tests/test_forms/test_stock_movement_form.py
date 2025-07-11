from django.test import TestCase
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovementReferenceType, StockMovementStatus
from inventory.forms.stock_movement_form import StockMovementForm

class StockMovementFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            address='123 Main St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_valid_form(self):
        data = {
            'reference_type': StockMovementReferenceType.PACKING_LIST,
            'reference_id': 123,
            'note': 'Test note',
            'warehouse': self.warehouse.id,
            'status': StockMovementStatus.DRAFT,
        }
        form = StockMovementForm(data=data)
        self.assertTrue(form.is_valid())
        movement = form.save(commit=False)
        movement.created_by = self.user
        movement.updated_by = self.user
        movement.save()
        self.assertEqual(movement.reference_type, StockMovementReferenceType.PACKING_LIST)
        self.assertEqual(movement.status, StockMovementStatus.DRAFT)
        self.assertEqual(movement.warehouse, self.warehouse)

    def test_invalid_form_missing_required(self):
        data = {
            'reference_type': '',
            'reference_id': '',
            'note': '',
            'warehouse': '',
            'status': '',
        }
        form = StockMovementForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('reference_type', form.errors)
        self.assertIn('warehouse', form.errors)
        self.assertIn('status', form.errors)
