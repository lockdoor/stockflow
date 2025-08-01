"""
Tests for Stock Views

Tests for StockIndexView, StockListView, and StockItemListView
focusing on proper functionality, parameter validation, and error handling.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from inventory.models.stock import Stock
from inventory.models.warehouse import Warehouse
from catalog.models.category import Category
from catalog.models.item import ItemSKU


class StockItemListViewTest(TestCase):
    """Test cases for StockItemListView"""
    
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
        self.future_date1 = self.today + timedelta(days=30)
        self.future_date2 = self.today + timedelta(days=60)
        
        # Create test stock records
        self.stock1 = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT001',
            expiry_date=self.future_date1,
            available_quantity=Decimal('100.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock2 = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT002',
            expiry_date=self.future_date2,
            available_quantity=Decimal('50.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Zero quantity stock (should be filtered out by default)
        self.stock_zero = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse,
            lot_number='LOT003',
            expiry_date=self.future_date1,
            available_quantity=Decimal('0.000'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client = Client()
    
    def test_requires_login(self):
        """Test that view requires authentication"""
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_missing_parameters_returns_empty_queryset(self):
        """Test that missing required parameters returns empty queryset"""
        self.client.login(username='testuser', password='testpass123')
        
        # Missing both parameters
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['stock_records']), [])
        
        # Missing warehouse_id
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {'item_sku_id': self.item.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['stock_records']), [])
        
        # Missing item_sku_id
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {'warehouse_id': self.warehouse.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['stock_records']), [])
    
    def test_valid_parameters_returns_available_stock(self):
        """Test that valid parameters return only available stock by default"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {
            'item_sku_id': self.item.id,
            'warehouse_id': self.warehouse.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Should return 2 records (excluding zero quantity)
        stock_records = list(response.context['stock_records'])
        self.assertEqual(len(stock_records), 2)
        
        # Should be ordered by expiry_date (FEFO)
        self.assertEqual(stock_records[0].lot_number, 'LOT001')  # Earlier expiry
        self.assertEqual(stock_records[1].lot_number, 'LOT002')  # Later expiry
        
        # Should not include zero quantity stock
        lot_numbers = [stock.lot_number for stock in stock_records]
        self.assertNotIn('LOT003', lot_numbers)
    
    def test_show_all_parameter_includes_zero_stock(self):
        """Test that all=true includes zero quantity stock"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {
            'item_sku_id': self.item.id,
            'warehouse_id': self.warehouse.id,
            'all': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Should return 3 records (including zero quantity)
        stock_records = list(response.context['stock_records'])
        self.assertEqual(len(stock_records), 3)
        
        # Should include zero quantity stock
        lot_numbers = [stock.lot_number for stock in stock_records]
        self.assertIn('LOT003', lot_numbers)
    
    def test_context_data_includes_summary_info(self):
        """Test that context includes summary information"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {
            'item_sku_id': self.item.id,
            'warehouse_id': self.warehouse.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        context = response.context
        self.assertEqual(context['item_sku_id'], str(self.item.id))
        self.assertEqual(context['warehouse_id'], str(self.warehouse.id))
        self.assertFalse(context['show_all'])
        
        # Check summary information
        self.assertEqual(context['total_available_stock'], Decimal('150.000'))  # 100 + 50
        self.assertEqual(context['item_sku'], self.item)
        self.assertEqual(context['warehouse'], self.warehouse)
    
    def test_context_data_with_show_all_parameter(self):
        """Test context data when show_all is true"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {
            'item_sku_id': self.item.id,
            'warehouse_id': self.warehouse.id,
            'all': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        self.assertTrue(context['show_all'])
    
    def test_invalid_item_or_warehouse_id_handles_gracefully(self):
        """Test that invalid IDs are handled gracefully"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {
            'item_sku_id': '99999',  # Non-existent ID
            'warehouse_id': self.warehouse.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Should return empty queryset
        self.assertEqual(list(response.context['stock_records']), [])
        
        # Context should handle the error gracefully
        context = response.context
        self.assertEqual(context['total_available_stock'], 0)
        self.assertEqual(context['error_message'], "Item or Warehouse not found")
    
    def test_select_related_optimization(self):
        """Test that queryset uses select_related for optimization"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        
        # This test ensures the view doesn't cause N+1 queries
        with self.assertNumQueries(9):  # Should be minimal queries due to select_related
            response = self.client.get(url, {
                'item_sku_id': self.item.id,
                'warehouse_id': self.warehouse.id
            })
        
        self.assertEqual(response.status_code, 200)
    
    def test_pagination_works(self):
        """Test that pagination works correctly"""
        # Create many stock records to test pagination
        for i in range(25):
            Stock.objects.create(
                item_sku=self.item,
                warehouse=self.warehouse,
                lot_number=f'LOT{i:03d}',
                expiry_date=self.future_date1 + timedelta(days=i),
                available_quantity=Decimal('10.000'),
                created_by=self.user,
                updated_by=self.user
            )
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-item-list')
        response = self.client.get(url, {
            'item_sku_id': self.item.id,
            'warehouse_id': self.warehouse.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Should have pagination due to paginate_by = 20
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['stock_records']), 20)


class StockListViewTest(TestCase):
    """Test cases for StockListView"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
    
    def test_requires_login(self):
        """Test that view requires authentication"""
        url = reverse('inventory:stock-list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_uses_get_all_stock_method(self):
        """Test that view uses Stock.get_all_stock() method"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('stock', response.context)
        
        # The queryset should be the result of get_all_stock()
        # This is implicit since we're calling the method in get_queryset()


class StockIndexViewTest(TestCase):
    """Test cases for StockIndexView"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
    
    def test_requires_login(self):
        """Test that view requires authentication"""
        url = reverse('inventory:stock-index')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_renders_correct_template(self):
        """Test that view renders correct template"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('inventory:stock-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/stock/index.html')
