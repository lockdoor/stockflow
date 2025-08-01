"""
Tests for Stock Model

Tests all functionality of the Stock model including:
- Basic CRUD operations
- Validation rules
- Business logic methods
- Query methods (get_all_stock, get_stock_for_item, etc.)
- FIFO/FEFO allocation logic

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta

from inventory.models.stock import Stock
from inventory.models.warehouse import Warehouse
from catalog.models.category import Category
from catalog.models.item import ItemSKU


class StockModelTest(TestCase):
    """Test cases for Stock model basic functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for stock tests',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test warehouses
        self.warehouse1 = Warehouse.objects.create(
            code='WH01',
            name='Main Warehouse',
            address='Building A',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.warehouse2 = Warehouse.objects.create(
            code='WH02', 
            name='Secondary Warehouse',
            address='Building B',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item SKUs
        self.item1 = ItemSKU.objects.create(
            sku_code='ITEM001',
            name='Test Item 1',
            unit='pcs',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            sku_code='ITEM002',
            name='Test Item 2', 
            unit='kg',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test dates
        self.today = date.today()
        self.future_date = self.today + timedelta(days=30)
        self.past_date = self.today - timedelta(days=30)
    
    def test_stock_creation(self):
        """Test basic stock record creation"""
        stock = Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(stock.item_sku, self.item1)
        self.assertEqual(stock.warehouse, self.warehouse1)
        self.assertEqual(stock.lot_number, 'LOT001')
        self.assertEqual(stock.expiry_date, self.future_date)
        self.assertEqual(stock.available_quantity, Decimal('100.000'))
    
    def test_stock_str_representation(self):
        """Test string representation of stock record"""
        stock = Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('50.500'),
            created_by=self.user,
            updated_by=self.user
        )
        
        expected = f"{self.item1.sku_code} @ {self.warehouse1.code} - Lot: LOT001 - Qty: 50.500"
        self.assertEqual(str(stock), expected)


class StockGetAllStockMethodTest(TestCase):
    """Test cases specifically for get_all_stock method"""
    
    def setUp(self):
        """Set up test data for get_all_stock tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for stock tests',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test warehouses
        self.warehouse1 = Warehouse.objects.create(
            code='WH01',
            name='Main Warehouse',
            address='Building A',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.warehouse2 = Warehouse.objects.create(
            code='WH02',
            name='Secondary Warehouse', 
            address='Building B',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item SKUs
        self.item1 = ItemSKU.objects.create(
            sku_code='ITEM001',
            name='Test Item 1',
            unit='pcs',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            sku_code='ITEM002', 
            name='Test Item 2',
            unit='kg',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test dates
        self.today = date.today()
        self.future_date = self.today + timedelta(days=30)
    
    def test_get_all_stock_empty_database(self):
        """Test get_all_stock when no stock records exist"""
        result = Stock.get_all_stock()
        
        self.assertEqual(list(result), [])
    
    def test_get_all_stock_single_record(self):
        """Test get_all_stock with single stock record"""
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['item_sku__id'], self.item1.id)
        self.assertEqual(result[0]['item_sku__sku_code'], 'ITEM001')
        self.assertEqual(result[0]['item_sku__name'], 'Test Item 1')
        self.assertEqual(result[0]['warehouse__id'], self.warehouse1.id) 
        self.assertEqual(result[0]['warehouse__code'], 'WH01')
        self.assertEqual(result[0]['total_quantity'], Decimal('100.000'))
    
    def test_get_all_stock_multiple_records_same_item_warehouse(self):
        """Test get_all_stock aggregates multiple lots of same item in same warehouse"""
        # Create multiple lots of same item in same warehouse
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('50.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT002',
            expiry_date=self.future_date + timedelta(days=10),
            available_quantity=Decimal('75.500'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['item_sku__sku_code'], 'ITEM001')
        self.assertEqual(result[0]['warehouse__code'], 'WH01')
        self.assertEqual(result[0]['total_quantity'], Decimal('125.500'))  # 50 + 75.5
    
    def test_get_all_stock_multiple_warehouses(self):
        """Test get_all_stock with same item in different warehouses"""
        # Same item in different warehouses
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse2,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('200.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        self.assertEqual(len(result), 2)
        
        # Should be ordered by warehouse code, then item sku code
        self.assertEqual(result[0]['warehouse__code'], 'WH01')
        self.assertEqual(result[0]['total_quantity'], Decimal('100.000'))
        
        self.assertEqual(result[1]['warehouse__code'], 'WH02')
        self.assertEqual(result[1]['total_quantity'], Decimal('200.000'))
    
    def test_get_all_stock_multiple_items(self):
        """Test get_all_stock with different items"""
        # Different items in same warehouse
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        Stock.objects.create(
            item_sku=self.item2,
            warehouse=self.warehouse1,
            lot_number='LOT002',
            expiry_date=self.future_date,
            available_quantity=Decimal('50.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        self.assertEqual(len(result), 2)
        
        # Should be ordered by warehouse code, then item sku code
        self.assertEqual(result[0]['item_sku__sku_code'], 'ITEM001')
        self.assertEqual(result[0]['total_quantity'], Decimal('100.000'))
        
        self.assertEqual(result[1]['item_sku__sku_code'], 'ITEM002')
        self.assertEqual(result[1]['total_quantity'], Decimal('50.000'))
    
    def test_get_all_stock_excludes_zero_quantity(self):
        """Test get_all_stock excludes records with zero quantity"""
        # Create stock with positive quantity
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock with zero quantity
        Stock.objects.create(
            item_sku=self.item2,
            warehouse=self.warehouse1,
            lot_number='LOT002',
            expiry_date=self.future_date,
            available_quantity=Decimal('0.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        # Should only return the record with positive quantity
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['item_sku__sku_code'], 'ITEM001')
        self.assertEqual(result[0]['total_quantity'], Decimal('100.000'))
    
    def test_get_all_stock_complex_scenario(self):
        """Test get_all_stock with complex real-world scenario"""
        # Create complex stock data:
        # ITEM001: WH01 (2 lots), WH02 (1 lot)
        # ITEM002: WH01 (1 lot), WH02 (0 quantity - should be excluded)
        
        # ITEM001 in WH01 - 2 lots
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('50.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT002',
            expiry_date=self.future_date + timedelta(days=10),
            available_quantity=Decimal('25.500'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # ITEM001 in WH02 - 1 lot
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse2,
            lot_number='LOT003',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # ITEM002 in WH01 - 1 lot
        Stock.objects.create(
            item_sku=self.item2,
            warehouse=self.warehouse1,
            lot_number='LOT004',
            expiry_date=self.future_date,
            available_quantity=Decimal('200.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # ITEM002 in WH02 - 0 quantity (should be excluded)
        Stock.objects.create(
            item_sku=self.item2,
            warehouse=self.warehouse2,
            lot_number='LOT005',
            expiry_date=self.future_date,
            available_quantity=Decimal('0.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        # Should return 3 aggregated records (excluding zero quantity)
        self.assertEqual(len(result), 3)
        
        # Check ordering: warehouse code first, then item sku code
        expected_results = [
            {
                'warehouse__code': 'WH01',
                'item_sku__sku_code': 'ITEM001',
                'total_quantity': Decimal('75.500')  # 50 + 25.5
            },
            {
                'warehouse__code': 'WH01', 
                'item_sku__sku_code': 'ITEM002',
                'total_quantity': Decimal('200.000')
            },
            {
                'warehouse__code': 'WH02',
                'item_sku__sku_code': 'ITEM001', 
                'total_quantity': Decimal('100.000')
            }
        ]
        
        for i, expected in enumerate(expected_results):
            self.assertEqual(result[i]['warehouse__code'], expected['warehouse__code'])
            self.assertEqual(result[i]['item_sku__sku_code'], expected['item_sku__sku_code'])
            self.assertEqual(result[i]['total_quantity'], expected['total_quantity'])
    
    def test_get_all_stock_includes_item_name(self):
        """Test get_all_stock includes item name in results"""
        Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        result = list(Stock.get_all_stock())
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['item_sku__name'], 'Test Item 1')
        self.assertIn('item_sku__name', result[0])


class StockBusinessLogicTest(TestCase):
    """Test cases for Stock model business logic methods"""
    
    def setUp(self):
        """Set up test data for business logic tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for stock tests',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test warehouse
        self.warehouse = Warehouse.objects.create(
            code='WH01',
            name='Test Warehouse',
            address='Building A',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item SKU
        self.item = ItemSKU.objects.create(
            sku_code='ITEM001',
            name='Test Item',
            unit='pcs',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test dates
        self.today = date.today()
        self.future_date = self.today + timedelta(days=30)
        self.past_date = self.today - timedelta(days=30)
    
    def test_is_expired_future_date(self):
        """Test is_expired method with future expiry date"""
        stock = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertFalse(stock.is_expired())
    
    def test_is_expired_past_date(self):
        """Test is_expired method with past expiry date"""
        stock = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.past_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(stock.is_expired())
    
    def test_days_to_expiry_future(self):
        """Test days_to_expiry with future date"""
        stock = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(stock.days_to_expiry(), 30)
    
    def test_days_to_expiry_past(self):
        """Test days_to_expiry with past date"""
        stock = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.past_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(stock.days_to_expiry(), -30)
    
    def test_is_available_positive_quantity(self):
        """Test is_available with positive quantity"""
        stock = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(stock.is_available())
    
    def test_is_available_zero_quantity(self):
        """Test is_available with zero quantity"""
        stock = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.future_date,
            available_quantity=Decimal('0.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertFalse(stock.is_available())
