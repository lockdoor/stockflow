"""
Test cases for Stock Item Detail View

Tests the StockItemDetailView functionality including:
- Authentication requirements
- Template rendering
- Context data for specific item
- Lot data grouped by warehouse
- Summary statistics
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import Http404
from decimal import Decimal

from inventory.models import Stock, Warehouse
from catalog.models.item import ItemSKU, Category
from inventory.views.stock_view import StockItemDetailView


User = get_user_model()


class StockItemDetailViewTestCase(TestCase):
    """Test cases for StockItemDetailView"""
    
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
        
        # Create test item
        self.item = ItemSKU.objects.create(
            sku_code='TEST001',
            name='Test Item',
            unit='PCS',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Activate after creation
        self.item.status = ItemSKU.Status.ACTIVE
        self.item.save()
        
        # Create test stocks for the item
        self.stock1 = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse1,
            lot_number='LOT001',
            available_quantity=Decimal('100.00'),
            expiry_date='2025-12-31',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock2 = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse1,
            lot_number='LOT002',
            available_quantity=Decimal('50.00'),
            expiry_date='2025-06-30',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock3 = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse2,
            lot_number='LOT003',
            available_quantity=Decimal('75.00'),
            expiry_date='2025-09-15',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Stock with zero quantity (should not appear)
        self.stock_zero = Stock.objects.create(
            item_sku=self.item,
            warehouse=self.warehouse2,
            lot_number='LOT004',
            available_quantity=Decimal('0.00'),
            expiry_date='2025-03-31',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another item for testing item not found
        self.other_item = ItemSKU.objects.create(
            sku_code='OTHER001',
            name='Other Item',
            unit='KG',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_view_accessible_when_logged_in(self):
        """Test that view is accessible when user is logged in"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Details by Warehouse')
        self.assertContains(response, self.item.name)
    
    def test_correct_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'inventory/stock/stock-item-detail.html')
    
    def test_nonexistent_item_returns_404(self):
        """Test that accessing non-existent item returns 404"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_context_contains_required_data(self):
        """Test that context contains all required data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        # Check required context variables
        self.assertIn('item', response.context)
        self.assertIn('warehouse_lots', response.context)
        self.assertIn('total_lots', response.context)
        self.assertIn('total_available', response.context)
        self.assertIn('warehouses_count', response.context)
        
        # Check item data
        self.assertEqual(response.context['item'].id, self.item.id)
        self.assertEqual(response.context['item'].sku_code, 'TEST001')
    
    def test_warehouse_lots_grouping(self):
        """Test that lots are correctly grouped by warehouse"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        warehouse_lots = response.context['warehouse_lots']
        
        # Should have 2 warehouses with stock
        self.assertEqual(len(warehouse_lots), 2)
        
        # Check warehouse1 has 2 lots
        wh1_lots = warehouse_lots[self.warehouse1]
        self.assertEqual(len(wh1_lots), 2)
        
        # Check lot details for warehouse1
        lot_numbers = [lot['lot_number'] for lot in wh1_lots]
        quantities = [lot['available_quantity'] for lot in wh1_lots]
        
        self.assertIn('LOT001', lot_numbers)
        self.assertIn('LOT002', lot_numbers)
        self.assertIn(Decimal('100.00'), quantities)
        self.assertIn(Decimal('50.00'), quantities)
        
        # Check warehouse2 has 1 lot (zero quantity lot should not appear)
        wh2_lots = warehouse_lots[self.warehouse2]
        self.assertEqual(len(wh2_lots), 1)
        self.assertEqual(wh2_lots[0]['lot_number'], 'LOT003')
        self.assertEqual(wh2_lots[0]['available_quantity'], Decimal('75.00'))
    
    def test_zero_quantity_lots_excluded(self):
        """Test that lots with zero available quantity are excluded"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        warehouse_lots = response.context['warehouse_lots']
        
        # Check that LOT004 (zero quantity) is not included
        all_lot_numbers = []
        for lots in warehouse_lots.values():
            for lot in lots:
                all_lot_numbers.append(lot['lot_number'])
        
        self.assertNotIn('LOT004', all_lot_numbers)
    
    def test_summary_statistics(self):
        """Test summary statistics calculations"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        # Check summary statistics
        self.assertEqual(response.context['total_lots'], 3)  # LOT001, LOT002, LOT003
        self.assertEqual(response.context['total_available'], Decimal('225.00'))  # 100 + 50 + 75
        self.assertEqual(response.context['warehouses_count'], 2)  # Main and Secondary
    
    def test_lots_ordered_correctly(self):
        """Test that lots are ordered by warehouse name and lot number"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        warehouse_lots = response.context['warehouse_lots']
        
        # Check warehouse1 lots are ordered by lot number
        wh1_lots = warehouse_lots[self.warehouse1]
        lot_numbers = [lot['lot_number'] for lot in wh1_lots]
        self.assertEqual(lot_numbers, ['LOT001', 'LOT002'])  # Alphabetical order
    
    def test_item_with_no_stock(self):
        """Test view behavior for item with no stock"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.other_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['warehouse_lots']), 0)
        self.assertEqual(response.context['total_lots'], 0)
        self.assertEqual(response.context['total_available'], 0)
        self.assertEqual(response.context['warehouses_count'], 0)
    
    def test_lot_data_includes_required_fields(self):
        """Test that lot data includes all required fields"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        warehouse_lots = response.context['warehouse_lots']
        
        # Check first lot has all required fields
        first_warehouse = list(warehouse_lots.keys())[0]
        first_lot = warehouse_lots[first_warehouse][0]
        
        required_fields = ['stock', 'lot_number', 'available_quantity', 'expiry_date']
        for field in required_fields:
            self.assertIn(field, first_lot)
        
        # Check that stock object is included
        self.assertIsInstance(first_lot['stock'], Stock)
    
    def test_view_method_get_warehouse_lots(self):
        """Test the get_warehouse_lots method directly"""
        view = StockItemDetailView()
        warehouse_lots = view.get_warehouse_lots(self.item)
        
        # Should return 2 warehouses
        self.assertEqual(len(warehouse_lots), 2)
        
        # Check data structure
        for warehouse, lots in warehouse_lots.items():
            self.assertIsInstance(warehouse, Warehouse)
            self.assertIsInstance(lots, list)
            
            for lot_data in lots:
                self.assertIn('stock', lot_data)
                self.assertIn('lot_number', lot_data)
                self.assertIn('available_quantity', lot_data)
                self.assertIn('expiry_date', lot_data)
    
    def test_view_method_get_item_summary(self):
        """Test the get_item_summary method directly"""
        view = StockItemDetailView()
        warehouse_lots = view.get_warehouse_lots(self.item)
        summary = view.get_item_summary(warehouse_lots)
        
        # Check summary structure
        required_fields = ['total_lots', 'total_available', 'warehouses_count']
        for field in required_fields:
            self.assertIn(field, summary)
        
        # Check summary values
        self.assertEqual(summary['total_lots'], 3)
        self.assertEqual(summary['total_available'], Decimal('225.00'))
        self.assertEqual(summary['warehouses_count'], 2)
    
    def test_optimized_query_performance(self):
        """Test that the view uses optimized queries"""
        self.client.login(username='testuser', password='testpass123')
        view = StockItemDetailView()
        
        # Should use minimal queries
        with self.assertNumQueries(1):  # Only one query for stocks with select_related
            warehouse_lots = view.get_warehouse_lots(self.item)
        
        self.assertGreater(len(warehouse_lots), 0)
    
    def test_expiry_date_display(self):
        """Test that expiry dates are correctly included"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        
        warehouse_lots = response.context['warehouse_lots']
        
        # Find lot with specific expiry date
        found_lot = None
        for lots in warehouse_lots.values():
            for lot in lots:
                if lot['lot_number'] == 'LOT001':
                    found_lot = lot
                    break
        
        self.assertIsNotNone(found_lot)
        self.assertEqual(str(found_lot['expiry_date']), '2025-12-31')
