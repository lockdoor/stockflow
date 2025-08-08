"""
Test Stock Alert Model

Tests for the StockAlert model including validation, business logic,
threshold calculations, and alert level determination.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from inventory.models.stock_alert import StockAlert
from inventory.models.warehouse import Warehouse
from catalog.models import ItemSKU, Category


class StockAlertModelTest(TestCase):
    """Test case for StockAlert model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a category for ItemSKU
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
            address="123 Storage St",
            created_by=self.user,
            updated_by=self.user
        )

    def test_stock_alert_creation_with_valid_data(self):
        """Test creating stock alert with valid data"""
        stock_alert = StockAlert(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            is_enabled=True,
            note="Test alert configuration",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should pass validation
        stock_alert.full_clean()
        
        # Save should work
        stock_alert.save()
        self.assertIsNotNone(stock_alert.pk)
        self.assertEqual(stock_alert.minimum_threshold, Decimal('100.00'))
        self.assertEqual(stock_alert.critical_threshold, Decimal('50.00'))

    def test_stock_alert_unique_constraint(self):
        """Test unique constraint on item_sku and warehouse combination"""
        # Create first alert
        StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # Should raise IntegrityError
            StockAlert.objects.create(
                item_sku=self.item_sku,
                warehouse=self.warehouse,
                minimum_threshold=Decimal('200.00'),
                critical_threshold=Decimal('100.00'),
                created_by=self.user,
                updated_by=self.user
            )

    def test_critical_threshold_validation(self):
        """Test that critical threshold must be <= minimum threshold"""
        stock_alert = StockAlert(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('50.00'),
            critical_threshold=Decimal('100.00'),  # Higher than minimum
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            stock_alert.full_clean()
        
        self.assertIn('critical_threshold', context.exception.error_dict)

    def test_negative_threshold_validation(self):
        """Test that thresholds cannot be negative"""
        # Test negative minimum threshold
        stock_alert = StockAlert(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('-10.00'),
            critical_threshold=Decimal('5.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            stock_alert.full_clean()
        
        # Test negative critical threshold
        stock_alert2 = StockAlert(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('10.00'),
            critical_threshold=Decimal('-5.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            stock_alert2.full_clean()

    def test_str_representation(self):
        """Test string representation of StockAlert"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        expected_str = f"Alert: {self.item_sku.sku_code} @ {self.warehouse.code} (Min: 100.00)"
        self.assertEqual(str(stock_alert), expected_str)

    def test_alert_levels_property(self):
        """Test alert_levels property returns correct dictionary"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        alert_levels = stock_alert.alert_levels
        self.assertEqual(alert_levels['minimum'], Decimal('100.00'))
        self.assertEqual(alert_levels['critical'], Decimal('50.00'))

    def test_is_stock_below_minimum(self):
        """Test is_stock_below_minimum method"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            is_enabled=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Stock below minimum
        self.assertTrue(stock_alert.is_stock_below_minimum(Decimal('80.00')))
        
        # Stock equal to minimum
        self.assertTrue(stock_alert.is_stock_below_minimum(Decimal('100.00')))
        
        # Stock above minimum
        self.assertFalse(stock_alert.is_stock_below_minimum(Decimal('120.00')))
        
        # Disabled alert should return False
        stock_alert.is_enabled = False
        self.assertFalse(stock_alert.is_stock_below_minimum(Decimal('80.00')))

    def test_is_stock_critical(self):
        """Test is_stock_critical method"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            is_enabled=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Stock below critical
        self.assertTrue(stock_alert.is_stock_critical(Decimal('30.00')))
        
        # Stock equal to critical
        self.assertTrue(stock_alert.is_stock_critical(Decimal('50.00')))
        
        # Stock above critical but below minimum
        self.assertFalse(stock_alert.is_stock_critical(Decimal('80.00')))
        
        # Stock above minimum
        self.assertFalse(stock_alert.is_stock_critical(Decimal('120.00')))
        
        # Disabled alert should return False
        stock_alert.is_enabled = False
        self.assertFalse(stock_alert.is_stock_critical(Decimal('30.00')))

    def test_get_alert_level(self):
        """Test get_alert_level method returns correct alert level"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            is_enabled=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Critical level
        self.assertEqual(stock_alert.get_alert_level(Decimal('30.00')), 'critical')
        self.assertEqual(stock_alert.get_alert_level(Decimal('50.00')), 'critical')
        
        # Warning level (เปลี่ยนจาก minimum เป็น warning)
        self.assertEqual(stock_alert.get_alert_level(Decimal('80.00')), 'warning')
        self.assertEqual(stock_alert.get_alert_level(Decimal('100.00')), 'warning')
        
        # Normal level
        self.assertEqual(stock_alert.get_alert_level(Decimal('120.00')), 'normal')
        
        # Disabled alert should return normal
        stock_alert.is_enabled = False
        self.assertEqual(stock_alert.get_alert_level(Decimal('30.00')), 'normal')

    def test_equal_thresholds(self):
        """Test when critical and minimum thresholds are equal"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('50.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should pass validation
        stock_alert.full_clean()
        
        # Both methods should return True at threshold
        self.assertTrue(stock_alert.is_stock_below_minimum(Decimal('50.00')))
        self.assertTrue(stock_alert.is_stock_critical(Decimal('50.00')))
        
        # get_alert_level should return critical (higher priority)
        self.assertEqual(stock_alert.get_alert_level(Decimal('50.00')), 'critical')

    def test_zero_thresholds(self):
        """Test with zero threshold values"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('0.00'),
            critical_threshold=Decimal('0.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should pass validation
        stock_alert.full_clean()
        
        # Test behavior with zero stock
        self.assertTrue(stock_alert.is_stock_below_minimum(Decimal('0.00')))
        self.assertTrue(stock_alert.is_stock_critical(Decimal('0.00')))
        self.assertEqual(stock_alert.get_alert_level(Decimal('0.00')), 'critical')
        
        # Any positive stock should be normal
        self.assertFalse(stock_alert.is_stock_below_minimum(Decimal('1.00')))
        self.assertFalse(stock_alert.is_stock_critical(Decimal('1.00')))
        self.assertEqual(stock_alert.get_alert_level(Decimal('1.00')), 'normal')

    def test_audit_fields_populated(self):
        """Test that audit fields are properly populated"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check audit fields
        self.assertEqual(stock_alert.created_by, self.user)
        self.assertEqual(stock_alert.updated_by, self.user)
        self.assertIsNotNone(stock_alert.created_at)
        self.assertIsNotNone(stock_alert.updated_at)
        self.assertIsNotNone(stock_alert.version)

    def test_related_name_access(self):
        """Test access via related names"""
        stock_alert = StockAlert.objects.create(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            minimum_threshold=Decimal('100.00'),
            critical_threshold=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test related access from ItemSKU
        item_alerts = self.item_sku.stock_alerts.all()
        self.assertIn(stock_alert, item_alerts)
        
        # Test related access from Warehouse
        warehouse_alerts = self.warehouse.stock_alerts.all()
        self.assertIn(stock_alert, warehouse_alerts)
