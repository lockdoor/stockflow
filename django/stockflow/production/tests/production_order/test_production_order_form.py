from django.test import TestCase
from production.forms.production_order_form import ProductionOrderForm
from tests.factories.inventory import WarehouseFactory
from tests.factories.user import AdminFactory
from production.models.production_order import ProductionOrder

class ProductionOrderFormTests(TestCase):
    def setUp(self):
        self.admin = AdminFactory()
        self.warehouse = WarehouseFactory(is_active=True, created_by=self.admin)
        self.inactive_warehouse = WarehouseFactory(created_by=self.admin)
        self.inactive_warehouse.is_active = False
        self.inactive_warehouse.save()

    def test_form_valid_with_minimal_data(self):
        form = ProductionOrderForm(data={
            'warehouse': self.warehouse.id,
            'note': '  Production order note  ',
            'status': ProductionOrder.Status.DRAFT
        })
        self.assertTrue(form.is_valid())
        cleaned = form.cleaned_data
        self.assertEqual(cleaned['warehouse'], self.warehouse)
        self.assertEqual(cleaned['note'], 'Production order note')

    def test_form_invalid_with_inactive_warehouse(self):
        form = ProductionOrderForm(data={
            'warehouse': self.inactive_warehouse.id,
            'note': 'Test',
            'status': ProductionOrder.Status.DRAFT
        })
        self.assertFalse(form.is_valid())
        self.assertIn('warehouse', form.errors)

    def test_form_note_blank_is_valid(self):
        form = ProductionOrderForm(data={
            'warehouse': self.warehouse.id,
            'note': '',
            'status': ProductionOrder.Status.DRAFT
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_note_whitespace_is_none(self):
        form = ProductionOrderForm(data={
            'warehouse': self.warehouse.id,
            'note': '   ',
            'status': ProductionOrder.Status.DRAFT
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_missing_warehouse_is_invalid(self):
        form = ProductionOrderForm(data={
            'note': 'Test',
            'status': ProductionOrder.Status.DRAFT
        })
        self.assertFalse(form.is_valid())
        self.assertIn('warehouse', form.errors)
