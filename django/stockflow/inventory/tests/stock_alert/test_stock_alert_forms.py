"""
Test Stock Alert Forms

Tests for StockAlert forms including validation, field handling,
and user interactions.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from inventory.forms.stock_alert_form import StockAlertForm, StockAlertSearchForm, BulkStockAlertForm
from inventory.models.stock_alert import StockAlert
from inventory.models.warehouse import Warehouse
from catalog.models import ItemSKU, Category


class StockAlertFormTest(TestCase):
    """Test case for StockAlertForm"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create category
        self.category = Category.objects.create(
            name="Test Category",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create ItemSKU
        self.item_sku = ItemSKU.objects.create(
            sku_code="ITEM001",
            name="Test Item",
            unit="PCS",
            type="RAW",
            status="ACTIVE",
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another ItemSKU (inactive) - use PRODUCT type to avoid validation
        self.inactive_item = ItemSKU.objects.create(
            sku_code="ITEM002",
            name="Inactive Item",
            unit="PCS",
            type="PRODUCT",  # Use PRODUCT instead of RAW to avoid validation
            status="INACTIVE",
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create Warehouse
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN01",
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_form_fields_present(self):
        """Test that all required fields are present"""
        form = StockAlertForm()
        
        expected_fields = [
            'item_sku', 'warehouse', 'minimum_threshold', 
            'critical_threshold', 'is_enabled', 'note'
        ]
        
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_form_queryset_filtering(self):
        """Test that querysets are properly filtered for active records"""
        form = StockAlertForm()
        
        # Should only include active items
        item_choices = list(form.fields['item_sku'].queryset)
        self.assertIn(self.item_sku, item_choices)
        self.assertNotIn(self.inactive_item, item_choices)
        
        # Should only include active warehouses
        warehouse_choices = list(form.fields['warehouse'].queryset)
        self.assertIn(self.warehouse, warehouse_choices)

    def test_valid_form_data(self):
        """Test form with valid data"""
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'minimum_threshold': '100.00',
            'critical_threshold': '50.00',
            'is_enabled': True,
            'note': 'Test alert configuration'
        }
        
        form = StockAlertForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_negative_threshold_validation(self):
        """Test validation of negative thresholds"""
        # Test negative minimum threshold
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'minimum_threshold': '-10.00',
            'critical_threshold': '50.00',
            'is_enabled': True,
        }
        
        form = StockAlertForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('minimum_threshold', form.errors)
        
        # Test negative critical threshold
        form_data['minimum_threshold'] = '100.00'
        form_data['critical_threshold'] = '-5.00'
        
        form = StockAlertForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('critical_threshold', form.errors)

    def test_critical_greater_than_minimum_validation(self):
        """Test validation when critical threshold > minimum threshold"""
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'minimum_threshold': '50.00',
            'critical_threshold': '100.00',  # Greater than minimum
            'is_enabled': True,
        }
        
        form = StockAlertForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('critical_threshold', form.errors)

    def test_duplicate_item_warehouse_validation(self):
        """Test validation for duplicate item-warehouse combination"""
        # Create existing alert
        StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'minimum_threshold': '200.00',
            'critical_threshold': '100.00',
            'is_enabled': True,
        }
        
        form = StockAlertForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_required_fields_validation(self):
        """Test validation of required fields"""
        form_data = {}
        form = StockAlertForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('item_sku', form.errors)
        self.assertIn('warehouse', form.errors)
        self.assertIn('minimum_threshold', form.errors)
        self.assertIn('critical_threshold', form.errors)

    def test_form_save_with_user(self):
        """Test saving form with user audit fields"""
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'minimum_threshold': '100.00',
            'critical_threshold': '50.00',
            'is_enabled': True,
            'note': 'Test alert'
        }
        
        form = StockAlertForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        stock_alert = form.save(user=self.user)
        
        self.assertEqual(stock_alert.created_by, self.user)
        self.assertEqual(stock_alert.updated_by, self.user)
        self.assertEqual(stock_alert.item_sku, self.item_sku)
        self.assertEqual(stock_alert.warehouse, self.warehouse)

    def test_equal_thresholds_valid(self):
        """Test that equal thresholds are valid"""
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'minimum_threshold': '50.00',
            'critical_threshold': '50.00',  # Equal to minimum
            'is_enabled': True,
        }
        
        form = StockAlertForm(data=form_data)
        self.assertTrue(form.is_valid())


class StockAlertSearchFormTest(TestCase):
    """Test case for StockAlertSearchForm"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create category
        self.category = Category.objects.create(
            name="Test Category",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create ItemSKU
        self.item_sku = ItemSKU.objects.create(
            sku_code="ITEM001",
            name="Test Item",
            unit="PCS",
            type="RAW",
            status="ACTIVE",
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create Warehouse
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN01",
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_search_form_fields(self):
        """Test search form has correct fields"""
        form = StockAlertSearchForm()
        
        expected_fields = ['item_sku', 'warehouse', 'is_enabled', 'search']
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_search_form_optional_fields(self):
        """Test that all search form fields are optional"""
        form = StockAlertSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_search_form_with_data(self):
        """Test search form with valid data"""
        form_data = {
            'item_sku': self.item_sku.pk,
            'warehouse': self.warehouse.pk,
            'is_enabled': 'true',
            'search': 'test search'
        }
        
        form = StockAlertSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


class BulkStockAlertFormTest(TestCase):
    """Test case for BulkStockAlertForm"""

    def test_bulk_form_fields(self):
        """Test bulk form has correct fields"""
        form = BulkStockAlertForm()
        
        self.assertIn('action', form.fields)
        self.assertIn('selected_alerts', form.fields)

    def test_valid_bulk_form_data(self):
        """Test bulk form with valid data"""
        form_data = {
            'action': 'enable',
            'selected_alerts': '1,2,3'
        }
        
        form = BulkStockAlertForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Check that selected_alerts are parsed correctly
        selected_ids = form.cleaned_data['selected_alerts']
        self.assertEqual(selected_ids, [1, 2, 3])

    def test_empty_selected_alerts_validation(self):
        """Test validation when no alerts are selected"""
        form_data = {
            'action': 'enable',
            'selected_alerts': ''
        }
        
        form = BulkStockAlertForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('selected_alerts', form.errors)

    def test_invalid_alert_ids_validation(self):
        """Test validation with invalid alert IDs"""
        form_data = {
            'action': 'enable',
            'selected_alerts': 'invalid,data'
        }
        
        form = BulkStockAlertForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('selected_alerts', form.errors)
