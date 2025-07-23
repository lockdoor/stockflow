"""
StockMovementByWarehouseListView Tests

Tests for StockMovementByWarehouseListView including pagination, filtering,
ordering, permissions, and edge cases.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import Http404
from datetime import datetime, timedelta
from django.utils import timezone

from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement


class StockMovementByWarehouseListViewTest(TestCase):
    """Test cases for StockMovementByWarehouseListView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='testpass')
        
        # Create warehouses with required fields
        self.warehouse1 = Warehouse.objects.create(
            name='Warehouse 1',
            code='WH01',
            address='123 Main St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.warehouse2 = Warehouse.objects.create(
            name='Warehouse 2',
            code='WH02',
            address='456 Oak Ave',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movements for warehouse1 (3 movements)
        for i in range(3):
            StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.PACKING_LIST,
                reference_id=100 + i,
                warehouse=self.warehouse1,
                note=f'Movement {i+1} for warehouse 1',
                created_by=self.user,
                updated_by=self.user,
                status=StockMovement.Status.CONFIRMED  # Use CONFIRMED to avoid unique constraint
            )
        
        # Create stock movements for warehouse2 (2 movements)  
        for i in range(2):
            StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.ADJUST,
                warehouse=self.warehouse2,
                note=f'Movement {i+1} for warehouse 2',
                created_by=self.user,
                updated_by=self.user,
                status=StockMovement.Status.CONFIRMED  # Use CONFIRMED to avoid unique constraint
            )

    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        url = reverse('inventory:stock-movement-list', args=[self.warehouse1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_list_view_for_warehouse1(self):
        """Test list view shows correct movements for warehouse1"""
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-movement-list', args=[self.warehouse1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/stock-movement/partials/stock-movement-list.html')
        self.assertEqual(len(response.context['stock_movements']), 3)
        
        # Verify all movements belong to warehouse1
        for movement in response.context['stock_movements']:
            self.assertEqual(movement.warehouse, self.warehouse1)
        
        # Verify warehouse context
        self.assertEqual(response.context['warehouse'], self.warehouse1)

    def test_list_view_for_warehouse2(self):
        """Test list view shows correct movements for warehouse2"""
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-movement-list', args=[self.warehouse2.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_movements']), 2)
        
        # Verify all movements belong to warehouse2
        for movement in response.context['stock_movements']:
            self.assertEqual(movement.warehouse, self.warehouse2)
        
        # Verify warehouse context
        self.assertEqual(response.context['warehouse'], self.warehouse2)

    def test_nonexistent_warehouse_returns_404(self):
        """Test that non-existent warehouse returns 404"""
        self.client.login(username='tester', password='testpass')
        url = reverse('inventory:stock-movement-list', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_missing_warehouse_id_returns_404(self):
        """Test that missing warehouse_id returns 404"""
        self.client.login(username='tester', password='testpass')
        # Test with invalid URL path (this will trigger 404 from URL pattern)
        response = self.client.get('/inventory/warehouses//stock-movements/')
        self.assertEqual(response.status_code, 404)

    def test_ordering_by_created_at_descending(self):
        """Test that movements are ordered by created_at descending (newest first)"""
        self.client.login(username='tester', password='testpass')
        
        # Create movements with specific timestamps using CONFIRMED status
        now = timezone.now()
        old_movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.PACKING_LIST,
            reference_id=200,
            warehouse=self.warehouse1,
            note='Old movement',
            created_by=self.user,
            updated_by=self.user,
            status=StockMovement.Status.CONFIRMED
        )
        # Update created_at to simulate older movement
        StockMovement.objects.filter(id=old_movement.id).update(
            created_at=now - timedelta(days=1)
        )
        
        new_movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.PACKING_LIST,
            reference_id=201,
            warehouse=self.warehouse1,
            note='New movement',
            created_by=self.user,
            updated_by=self.user,
            status=StockMovement.Status.CONFIRMED
        )
        
        url = reverse('inventory:stock-movement-list', args=[self.warehouse1.id])
        response = self.client.get(url)
        
        movements = list(response.context['stock_movements'])
        # Check that newer movement comes first
        self.assertEqual(movements[0].note, 'New movement')


class StockMovementByWarehouseListViewPaginationTest(TestCase):
    """Test pagination functionality"""
    
    def setUp(self):
        """Set up test data for pagination"""
        self.client = Client()
        self.user = User.objects.create_user(username='paginationuser', password='testpass')
        
        self.warehouse = Warehouse.objects.create(
            name='Pagination Warehouse',
            code='PAGINATE01',
            address='123 Pagination St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create 25 movements to test pagination (page size is 20)
        # Use CONFIRMED status and unique reference_ids to avoid constraint issues
        for i in range(25):
            StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.PACKING_LIST,
                reference_id=300 + i,  # Unique reference_id for each
                warehouse=self.warehouse,
                note=f'Movement {i+1}',
                created_by=self.user,
                updated_by=self.user,
                status=StockMovement.Status.CONFIRMED
            )
        
        self.url = reverse('inventory:stock-movement-list', args=[self.warehouse.id])
    
    def test_pagination_first_page(self):
        """Test first page shows 20 items"""
        self.client.login(username='paginationuser', password='testpass')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_movements']), 20)
        
        # Check pagination context
        page_obj = response.context['page_obj']
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())
        self.assertEqual(page_obj.number, 1)
        self.assertEqual(page_obj.paginator.num_pages, 2)
    
    def test_pagination_second_page(self):
        """Test second page shows remaining items"""
        self.client.login(username='paginationuser', password='testpass')
        
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_movements']), 5)  # Remaining 5 items
        
        # Check pagination context
        page_obj = response.context['page_obj']
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())
        self.assertEqual(page_obj.number, 2)
    
    def test_pagination_invalid_page(self):
        """Test invalid page number returns 404"""
        self.client.login(username='paginationuser', password='testpass')
        
        response = self.client.get(self.url, {'page': 999})
        self.assertEqual(response.status_code, 404)  # Django raises 404 for invalid page
    
    def test_pagination_non_integer_page(self):
        """Test non-integer page parameter returns 404"""
        self.client.login(username='paginationuser', password='testpass')
        
        response = self.client.get(self.url, {'page': 'invalid'})
        self.assertEqual(response.status_code, 404)  # Django raises 404 for non-integer page


class StockMovementByWarehouseListViewContextTest(TestCase):
    """Test context data and template usage"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='contextuser', password='testpass')
        
        self.warehouse = Warehouse.objects.create(
            name='Context Warehouse',
            code='CONTEXT01',
            address='123 Context St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a few movements with CONFIRMED status
        for i in range(3):
            StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.PACKING_LIST,
                reference_id=400 + i,
                warehouse=self.warehouse,
                note=f'Context movement {i+1}',
                created_by=self.user,
                updated_by=self.user,
                status=StockMovement.Status.CONFIRMED
            )
        
        self.url = reverse('inventory:stock-movement-list', args=[self.warehouse.id])
    
    def test_context_object_name(self):
        """Test that context_object_name is set correctly"""
        self.client.login(username='contextuser', password='testpass')
        
        response = self.client.get(self.url)
        self.assertIn('stock_movements', response.context)
        self.assertEqual(len(response.context['stock_movements']), 3)
    
    def test_warehouse_in_context(self):
        """Test that warehouse is included in context"""
        self.client.login(username='contextuser', password='testpass')
        
        response = self.client.get(self.url)
        self.assertIn('warehouse', response.context)
        self.assertEqual(response.context['warehouse'], self.warehouse)
    
    def test_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='contextuser', password='testpass')
        
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'inventory/stock-movement/partials/stock-movement-list.html')
    
    def test_empty_queryset(self):
        """Test behavior with empty queryset"""
        # Create warehouse with no movements
        empty_warehouse = Warehouse.objects.create(
            name='Empty Warehouse',
            code='EMPTY01',
            address='123 Empty St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='contextuser', password='testpass')
        
        url = reverse('inventory:stock-movement-list', args=[empty_warehouse.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_movements']), 0)
        self.assertEqual(response.context['warehouse'], empty_warehouse)
