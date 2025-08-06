"""
Test cases for Stock Overview View

Tests the StockOverviewView functionality including:
- Authentication requirements
- Template rendering
- Context data
- Query optimization
- Frontend search data
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Sum
from decimal import Decimal
import json

from inventory.models import Stock, Warehouse
from catalog.models.item import ItemSKU, Category
from inventory.views.stock_view import StockOverviewView


User = get_user_model()


class StockOverviewViewTestCase(TestCase):
    """Test cases for StockOverviewView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test warehouses
        self.warehouse1 = Warehouse.objects.create(
            name='Main Warehouse',
            code='MAIN',
            address='123 Main St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.warehouse2 = Warehouse.objects.create(
            name='Secondary Warehouse',
            code='SEC',
            address='456 Second St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create inactive warehouse separately to avoid validation issues
        self.warehouse_inactive = Warehouse(
            name='Inactive Warehouse',
            code='INACTIVE',
            address='789 Inactive St',
            is_active=True,  # Create as active first
            created_by=self.user,
            updated_by=self.user
        )
        self.warehouse_inactive.save()
        # Then update to inactive
        self.warehouse_inactive.is_active = False
        self.warehouse_inactive.save()
        
        # Create test items
        self.item1 = ItemSKU.objects.create(
            sku_code='ITEM001',
            name='Test Item 1',
            unit='PCS',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start as DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Activate after creation
        self.item1.status = ItemSKU.Status.ACTIVE
        self.item1.save()
        
        self.item2 = ItemSKU.objects.create(
            sku_code='ITEM002',
            name='Test Item 2',
            unit='KG',
            type=ItemSKU.Type.RAW,  # Use RAW instead of MATERIAL
            status=ItemSKU.Status.ACTIVE,  # RAW can start as ACTIVE
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item_inactive = ItemSKU.objects.create(
            sku_code='ITEM003',
            name='Inactive Item',
            unit='PCS',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start as DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Set to inactive after creation
        self.item_inactive.status = ItemSKU.Status.INACTIVE
        self.item_inactive.save()
        
        # Create test stocks
        self.stock1_wh1 = Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            available_quantity=Decimal('100.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock1_wh2 = Stock.objects.create(
            item_sku=self.item1,
            warehouse=self.warehouse2,
            lot_number='LOT002',
            available_quantity=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock2_wh1 = Stock.objects.create(
            item_sku=self.item2,
            warehouse=self.warehouse1,
            lot_number='LOT003',
            available_quantity=Decimal('25.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Stock with zero available quantity (should not appear)
        self.stock_zero = Stock.objects.create(
            item_sku=self.item2,
            warehouse=self.warehouse2,
            lot_number='LOT004',
            available_quantity=Decimal('0.00'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Note: We don't create stock for inactive item or inactive warehouse 
        # as they're not allowed by business rules
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_view_accessible_when_logged_in(self):
        """Test that view is accessible when user is logged in"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Overview')
    
    def test_correct_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'inventory/stock/stock-overview.html')
    
    def test_context_contains_required_data(self):
        """Test that context contains all required data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        # Check required context variables
        self.assertIn('warehouses', response.context)
        self.assertIn('stock_overview', response.context)
        self.assertIn('stock_data_json', response.context)
        self.assertIn('total_items', response.context)
        self.assertIn('total_stock_value', response.context)
        self.assertIn('low_stock_count', response.context)
        self.assertIn('active_warehouses', response.context)
    
    def test_warehouses_context(self):
        """Test that warehouses context contains only active warehouses"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        warehouses = response.context['warehouses']
        warehouse_names = [wh.name for wh in warehouses]
        
        self.assertIn('Main Warehouse', warehouse_names)
        self.assertIn('Secondary Warehouse', warehouse_names)
        self.assertNotIn('Inactive Warehouse', warehouse_names)
    
    def test_stock_overview_data_content(self):
        """Test stock overview data contains correct items and quantities"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        stock_overview = response.context['stock_overview']
        
        # Should have 2 items (item1 and item2)
        # item_inactive should not appear (inactive status)
        # item2 in warehouse2 should not contribute (zero available quantity)
        self.assertEqual(len(stock_overview), 2)
        
        # Find item1 data
        item1_data = next((item for item in stock_overview if item['item'].id == self.item1.id), None)
        self.assertIsNotNone(item1_data)
        self.assertEqual(item1_data['total_quantity'], Decimal('150.00'))  # 100 + 50
        
        # Check warehouse distribution for item1
        item1_warehouses = {wh['warehouse__name']: wh['total_quantity'] for wh in item1_data['warehouses']}
        self.assertEqual(item1_warehouses['Main Warehouse'], 100)
        self.assertEqual(item1_warehouses['Secondary Warehouse'], 50)
        
        # Find item2 data
        item2_data = next((item for item in stock_overview if item['item'].id == self.item2.id), None)
        self.assertIsNotNone(item2_data)
        self.assertEqual(item2_data['total_quantity'], Decimal('25.00'))  # Only from warehouse1
        
        # Check warehouse distribution for item2
        item2_warehouses = {wh['warehouse__name']: wh['total_quantity'] for wh in item2_data['warehouses']}
        self.assertEqual(item2_warehouses['Main Warehouse'], 25)
        self.assertNotIn('Secondary Warehouse', item2_warehouses)  # Zero quantity
    
    def test_stock_data_json_format(self):
        """Test that JSON data is properly formatted for frontend"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        stock_data_json = json.loads(response.context['stock_data_json'])
        
        # Should have 2 items
        self.assertEqual(len(stock_data_json), 2)
        
        # Check item1 JSON structure
        item1_json = next((item for item in stock_data_json if item['id'] == self.item1.id), None)
        self.assertIsNotNone(item1_json)
        
        required_fields = ['id', 'sku_code', 'name', 'unit', 'type', 'category', 'total_quantity', 'warehouses']
        for field in required_fields:
            self.assertIn(field, item1_json)
        
        # Check warehouse quantities in JSON
        self.assertEqual(item1_json['warehouses']['MAIN'], 100.0)
        self.assertEqual(item1_json['warehouses']['SEC'], 50.0)
        self.assertEqual(item1_json['total_quantity'], 150.0)
    
    def test_summary_statistics(self):
        """Test summary statistics calculations"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        # Check summary statistics
        self.assertEqual(response.context['total_items'], 2)  # item1 and item2
        self.assertEqual(response.context['total_stock_value'], Decimal('175.00'))  # 150 + 25
        self.assertEqual(response.context['active_warehouses'], 2)  # Main and Secondary
        
        # Low stock count (items with quantity < 10)
        # item1: 150 (not low), item2: 25 (not low)
        self.assertEqual(response.context['low_stock_count'], 0)
    
    def test_low_stock_detection(self):
        """Test low stock detection logic"""
        # Create item with low stock
        low_stock_item = ItemSKU.objects.create(
            sku_code='LOW001',
            name='Low Stock Item',
            unit='PCS',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start as DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Activate after creation
        low_stock_item.status = ItemSKU.Status.ACTIVE
        low_stock_item.save()
        
        Stock.objects.create(
            item_sku=low_stock_item,
            warehouse=self.warehouse1,
            lot_number='LOW_LOT',
            available_quantity=Decimal('5.00'),  # Low stock
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        # Should now have 1 low stock item
        self.assertEqual(response.context['low_stock_count'], 1)
    
    def test_optimized_query_performance(self):
        """Test that the view uses optimized queries"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test the view method directly
        view = StockOverviewView()
        
        with self.assertNumQueries(2):  # Should be minimal queries
            # 1. Get warehouses
            # 2. Get items with annotations (includes category select_related)
            stock_data = view.get_optimized_stock_data()
        
        self.assertIn('items', stock_data)
        self.assertIn('json_data', stock_data)
    
    def test_view_handles_no_stock_data(self):
        """Test view behavior when no stock data exists"""
        # Delete all stocks
        Stock.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_overview']), 0)
        self.assertEqual(response.context['total_items'], 0)
        self.assertEqual(response.context['total_stock_value'], 0)
    
    def test_items_ordered_by_total_quantity_desc(self):
        """Test that items are ordered by total quantity descending"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        stock_overview = response.context['stock_overview']
        
        # Should be ordered: item1 (150) then item2 (25)
        self.assertEqual(stock_overview[0]['item'].id, self.item1.id)
        self.assertEqual(stock_overview[1]['item'].id, self.item2.id)
        
        # Verify quantities are in descending order
        quantities = [item['total_quantity'] for item in stock_overview]
        self.assertEqual(quantities, sorted(quantities, reverse=True))
    
    def test_only_active_items_included(self):
        """Test that only active items are included in results"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        stock_overview = response.context['stock_overview']
        item_ids = [item['item'].id for item in stock_overview]
        
        # Active items should be included
        self.assertIn(self.item1.id, item_ids)
        self.assertIn(self.item2.id, item_ids)
        
        # Inactive item should not be included
        self.assertNotIn(self.item_inactive.id, item_ids)
    
    def test_only_positive_available_quantity_included(self):
        """Test that only items with positive available quantity are included"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-overview')
        response = self.client.get(url)
        
        stock_overview = response.context['stock_overview']
        
        # All items should have positive total quantity
        for item_data in stock_overview:
            self.assertGreater(item_data['total_quantity'], 0)
            
            # All warehouse quantities should be positive
            for warehouse_data in item_data['warehouses']:
                self.assertGreater(warehouse_data['total_quantity'], 0)
