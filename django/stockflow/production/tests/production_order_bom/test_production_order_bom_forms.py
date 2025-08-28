from django.test import TestCase
from production.forms.production_order_bom_form import ProductionOrderBOMForm
from tests.factories.production import ProductionOrderFactory
from tests.factories.catalog import ItemFactory, ProductFactory
from tests.factories.user import AdminFactory
from tests.factories.inventory import WarehouseFactory

class ProductionOrderBOMFormTests(TestCase):
    def setUp(self):
        self.admin = AdminFactory()
        self.factory = WarehouseFactory(created_by=self.admin)
        self.production_order = ProductionOrderFactory(warehouse=self.factory, created_by=self.admin)
        self.product = ProductFactory(created_by=self.admin)

    def test_form_valid_with_minimal_data(self):
        form = ProductionOrderBOMForm(data={
            'item_sku': self.product,
            'planned_quantity': 5,
            'note': '  BOM note  ',
        }, production_order=self.production_order)
        print(form.errors)
        self.assertTrue(form.is_valid())
        cleaned = form.cleaned_data
        self.assertEqual(cleaned['item_sku'], self.product)
        self.assertEqual(cleaned['planned_quantity'], 5)
        self.assertEqual(cleaned['note'], 'BOM note')
        instance = form.save(commit=False)
        self.assertEqual(instance.production_order, self.production_order)

    def test_form_note_blank_is_valid(self):
        form = ProductionOrderBOMForm(data={
            'item_sku': self.product,
            'planned_quantity': 1,
            'note': '',
        }, production_order=self.production_order)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_missing_item_sku_is_invalid(self):
        form = ProductionOrderBOMForm(data={
            'planned_quantity': 1,
            'note': 'Test',
        }, production_order=self.production_order)
        with self.assertRaises(Exception):
            form.is_valid()

    def test_form_missing_production_order_raises(self):
        form = ProductionOrderBOMForm(data={
            'item_sku': self.product,
            'planned_quantity': 1,
            'note': 'Test',
        })
        # production_order is required for instance to be valid
        with self.assertRaises(Exception):
            form.save(commit=False)
