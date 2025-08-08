"""
Test cases for Stock Item Movement History View

Tests the StockItemMovementHistoryView functionality including:
- Authentication requirements
- Template rendering
- Context data for movement history
- Filtering by warehouse and lot
- Movement items ordering
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import Http404
from decimal import Decimal
from datetime import date

from inventory.models import Stock, Warehouse
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from catalog.models.item import ItemSKU, Category
from inventory.views.stock_view import StockItemMovementHistoryView


User = get_user_model()


class StockItemMovementHistoryViewTestCase(TestCase):
    """Test cases for StockItemMovementHistoryView"""
    
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
            created_by=self.user,
            updated_by=self.user
        )
        
        self.warehouse2 = Warehouse.objects.create(
            name='Secondary Warehouse',
            code='SEC',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test item
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='PCS',
            type='RAW',  # Use RAW material type which allows ACTIVE status
            status='ACTIVE',  # ACTIVE status for RAW material
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test stock movements
        self.stock_movement1 = StockMovement.objects.create(
            warehouse=self.warehouse1,
            reference_type='RECEIPT',
            reference_id=None,
            status='DRAFT',  # Change to DRAFT so we can add items
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock_movement2 = StockMovement.objects.create(
            warehouse=self.warehouse2,
            reference_type='ADJUSTMENT',
            reference_id=None,
            status='DRAFT',  # Change to DRAFT so we can add items
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test movement items
        self.movement_item1 = StockMovementItem.objects.create(
            stock_movement=self.stock_movement1,
            item_sku=self.item,
            movement_type='IN',
            quantity=Decimal('100.00'),
            lot_number='LOT-001',
            expiry_date=date(2025, 12, 31),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.movement_item2 = StockMovementItem.objects.create(
            stock_movement=self.stock_movement1,
            item_sku=self.item,
            movement_type='OUT',
            quantity=Decimal('50.00'),
            lot_number='LOT-001',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.movement_item3 = StockMovementItem.objects.create(
            stock_movement=self.stock_movement2,
            item_sku=self.item,
            movement_type='IN',
            quantity=Decimal('75.00'),
            lot_number='LOT-002',
            expiry_date=date(2026, 6, 30),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create another item for testing filtering
        self.other_item = ItemSKU.objects.create(
            sku_code='OTHER-001',
            name='Other Item',
            unit='PCS',
            type='RAW',  # Change to RAW type for ACTIVE status
            status='ACTIVE',  # Change to ACTIVE status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.other_movement_item = StockMovementItem.objects.create(
            stock_movement=self.stock_movement1,
            item_sku=self.other_item,
            movement_type='IN',
            quantity=Decimal('25.00'),
            lot_number='OTHER-LOT',
            created_by=self.user,
            updated_by=self.user
        )
        
        # URL for the view
        self.url = reverse('inventory:stock-item-movement-history', kwargs={'item_id': self.item.id})
    
    def test_view_requires_authentication(self):
        """Test that view requires user authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_view_with_invalid_item_id_returns_404(self):
        """Test that view returns 404 for non-existent item"""
        self.client.login(username='testuser', password='testpass123')
        
        invalid_url = reverse('inventory:stock-item-movement-history', kwargs={'item_id': 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_view_uses_correct_template(self):
        """Test that view uses the correct template"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/stock/stock-item-movement-history.html')
    
    def test_view_context_contains_required_data(self):
        """Test that view context contains all required data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Check that required context variables are present
        self.assertIn('item', response.context)
        self.assertIn('movement_items', response.context)
        self.assertIn('warehouse_filter', response.context)
        self.assertIn('lot_filter', response.context)
        
        # Check item data
        self.assertEqual(response.context['item'], self.item)
    
    def test_movement_items_filtered_by_item(self):
        """Test that movement items are correctly filtered by item"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.url)
        movement_items = response.context['movement_items']
        
        # Should only show movement items for this item (3 items)
        self.assertEqual(movement_items.count(), 3)
        
        # Check that all items belong to the correct item
        for movement_item in movement_items:
            self.assertEqual(movement_item.item_sku, self.item)
    
    def test_movement_items_ordering(self):
        """Test that movement items are ordered correctly (newest first)"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.url)
        movement_items = list(response.context['movement_items'])
        
        # Check that items are ordered by creation date (newest first)
        for i in range(len(movement_items) - 1):
            self.assertGreaterEqual(
                movement_items[i].stock_movement.created_at,
                movement_items[i + 1].stock_movement.created_at
            )
    
    def test_warehouse_filter(self):
        """Test filtering by warehouse"""
        self.client.login(username='testuser', password='testpass123')
        
        # Filter by warehouse1
        response = self.client.get(self.url, {'warehouse': self.warehouse1.id})
        movement_items = response.context['movement_items']
        
        # Should only show items from warehouse1 (2 items)
        self.assertEqual(movement_items.count(), 2)
        for movement_item in movement_items:
            self.assertEqual(movement_item.stock_movement.warehouse, self.warehouse1)
        
        # Check context
        self.assertEqual(response.context['warehouse_filter'], str(self.warehouse1.id))
        self.assertEqual(response.context['warehouse_name'], self.warehouse1.name)
    
    def test_lot_filter(self):
        """Test filtering by lot number"""
        self.client.login(username='testuser', password='testpass123')
        
        # Filter by LOT-001
        response = self.client.get(self.url, {'lot': 'LOT-001'})
        movement_items = response.context['movement_items']
        
        # Should only show items from LOT-001 (2 items)
        self.assertEqual(movement_items.count(), 2)
        for movement_item in movement_items:
            self.assertEqual(movement_item.lot_number, 'LOT-001')
        
        # Check context
        self.assertEqual(response.context['lot_filter'], 'LOT-001')
    
    def test_combined_warehouse_and_lot_filter(self):
        """Test filtering by both warehouse and lot"""
        self.client.login(username='testuser', password='testpass123')
        
        # Filter by warehouse1 and LOT-001
        response = self.client.get(self.url, {
            'warehouse': self.warehouse1.id,
            'lot': 'LOT-001'
        })
        movement_items = response.context['movement_items']
        
        # Should only show items from warehouse1 with LOT-001 (2 items)
        self.assertEqual(movement_items.count(), 2)
        for movement_item in movement_items:
            self.assertEqual(movement_item.stock_movement.warehouse, self.warehouse1)
            self.assertEqual(movement_item.lot_number, 'LOT-001')
    
    def test_invalid_warehouse_filter(self):
        """Test that invalid warehouse filter doesn't break the view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Use invalid warehouse ID
        response = self.client.get(self.url, {'warehouse': 99999})
        self.assertEqual(response.status_code, 200)
        
        # Should show all items (no filtering)
        movement_items = response.context['movement_items']
        self.assertEqual(movement_items.count(), 3)
        
        # warehouse_name should not be in context
        self.assertNotIn('warehouse_name', response.context)
    
    def test_no_movement_items_for_item(self):
        """Test view when item has no movement items"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create new item without movement items
        new_item = ItemSKU.objects.create(
            sku_code='NO-MOVES',
            name='No Movements Item',
            unit='PCS',
            type='PRODUCT',
            status='DRAFT',  # Start as DRAFT for PRODUCT type
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('inventory:stock-item-movement-history', kwargs={'item_id': new_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['movement_items'].count(), 0)
    
    def test_view_class_attributes(self):
        """Test that view class has correct attributes"""
        view = StockItemMovementHistoryView()
        self.assertEqual(view.template_name, 'inventory/stock/stock-item-movement-history.html')
    
    def test_get_movement_items_method(self):
        """Test the get_movement_items method directly"""
        view = StockItemMovementHistoryView()
        view.request = self.client.get(self.url).wsgi_request
        view.kwargs = {'item_id': self.item.id}
        
        # Test without filters
        movement_items = view.get_movement_items(self.item)
        self.assertEqual(movement_items.count(), 3)
        
        # Test with warehouse filter
        view.request = self.client.get(self.url, {'warehouse': self.warehouse1.id}).wsgi_request
        movement_items = view.get_movement_items(self.item)
        self.assertEqual(movement_items.count(), 2)
        
        # Test with lot filter
        view.request = self.client.get(self.url, {'lot': 'LOT-001'}).wsgi_request
        movement_items = view.get_movement_items(self.item)
        self.assertEqual(movement_items.count(), 2)


class StockItemMovementHistoryViewIntegrationTestCase(TestCase):
    """Integration tests for StockItemMovementHistoryView"""
    
    def setUp(self):
        """Set up test data for integration tests"""
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
        
        # Create test item
        self.item = ItemSKU.objects.create(
            sku_code='INT-TEST-001',
            name='Integration Test Item',
            unit='PCS',
            type='PRODUCT',
            status='DRAFT',  # Start as DRAFT for PRODUCT type
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('inventory:stock-item-movement-history', kwargs={'item_id': self.item.id})
    
    def test_url_resolves_correctly(self):
        """Test that URL resolves to correct view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.view_class, StockItemMovementHistoryView)
    
    def test_breadcrumb_navigation_links(self):
        """Test that template contains proper navigation links"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.url)
        content = response.content.decode()
        
        # Check for back to stock details link
        expected_link = reverse('inventory:stock-item-detail', kwargs={'item_id': self.item.id})
        self.assertIn(expected_link, content)
        self.assertIn('Back to Stock Details', content)
