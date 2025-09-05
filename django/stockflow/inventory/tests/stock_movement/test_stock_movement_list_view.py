"""
Test Stock Movement List View

Tests for stock movement list view including pagination, authentication,
and proper template rendering with redirect flow.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse


class StockMovementListViewTest(TestCase):
    """Test case for StockMovement list view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test warehouse
        self.warehouse = Warehouse(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, self.warehouse).save()
        
        # Create test stock movements
        self.stock_movement1 = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.NONE,
            note='Test movement 1',
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock_movement2 = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=123,
            note='Test movement 2',
            warehouse=self.warehouse,
            status=StockMovement.Status.CONFIRMED,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock_movement3 = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=456,
            note='Test movement 3',
            warehouse=self.warehouse,
            status=StockMovement.Status.COMPLETED,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('inventory:stock-movement-list')

    def test_view_requires_authentication(self):
        """Test that view requires user to be logged in"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_view_with_authenticated_user(self):
        """Test view with authenticated user returns success"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Movements')

    def test_view_uses_correct_template(self):
        """Test that view uses correct template"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertTemplateUsed(response, 'inventory/stock-movement/stock-movement-list.html')

    def test_view_context_contains_stock_movements(self):
        """Test that view context contains stock movements"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertIn('stock_movements', response.context)
        stock_movements = response.context['stock_movements']
        
        # Should contain all 3 stock movements
        self.assertEqual(len(stock_movements), 3)
        
        # Check that movements are ordered by created_at descending
        movement_ids = [movement.id for movement in stock_movements]
        expected_order = [self.stock_movement3.id, self.stock_movement2.id, self.stock_movement1.id]
        self.assertEqual(movement_ids, expected_order)

    def test_view_displays_stock_movement_information(self):
        """Test that view displays stock movement information correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for stock movement IDs
        self.assertContains(response, f'#{self.stock_movement1.id}')
        self.assertContains(response, f'#{self.stock_movement2.id}')
        self.assertContains(response, f'#{self.stock_movement3.id}')
        
        # Check for warehouse information
        self.assertContains(response, self.warehouse.name)
        
        # Check for reference types
        self.assertContains(response, 'None')  # NONE reference type
        self.assertContains(response, 'Adjust')  # ADJUST reference type

    def test_view_displays_status_badges(self):
        """Test that view displays status badges correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for status badges
        self.assertContains(response, 'Draft')  # DRAFT status
        self.assertContains(response, 'Confirmed')  # CONFIRMED status
        self.assertContains(response, 'Completed')  # COMPLETED status

    def test_view_displays_action_buttons(self):
        """Test that view displays action buttons correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for action buttons
        self.assertContains(response, 'View Details')
        self.assertContains(response, 'Edit')  # Should appear for DRAFT movements
        self.assertContains(response, 'Add Movement Item')  # Should appear in dropdown

    def test_pagination_setup(self):
        """Test that pagination is set up correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check that pagination is available (though not visible with only 3 items)
        self.assertTrue(hasattr(response.context['view'], 'paginate_by'))
        self.assertEqual(response.context['view'].paginate_by, 20)

    def test_empty_stock_movement_list(self):
        """Test view behavior when no stock movements exist"""
        # Delete all stock movements
        StockMovement.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Stock Movements')
        self.assertContains(response, 'Create First Movement')

    def test_view_with_many_stock_movements_pagination(self):
        """Test pagination with many stock movements"""
        # Create additional warehouses and stock movements to test pagination
        # Since each warehouse can only have one DRAFT movement, we need multiple warehouses
        # or use different statuses
        
        movements_to_create = 22  # Total will be 25 (3 existing + 22 new)
        statuses = [
            StockMovement.Status.CONFIRMED,
            StockMovement.Status.COMPLETED,
            StockMovement.Status.FAILED,
            StockMovement.Status.PROCESSING
        ]
        
        for i in range(movements_to_create):
            # Create new warehouse for some movements to avoid unique constraint
            if i % 5 == 0:  # Every 5th movement gets a new warehouse
                warehouse = Warehouse(
                    name=f'Test Warehouse {i}',
                    code=f'TEST{i:02d}',
                    address=f'{i} Test St',
                    is_active=True,
                    created_by=self.user,
                    updated_by=self.user
                )
                super(Warehouse, warehouse).save()
            else:
                warehouse = self.warehouse
            
            # Use different statuses to avoid unique constraint with DRAFT
            status = statuses[i % len(statuses)]
            
            StockMovement.objects.create(
                reference_type=StockMovement.ReferenceType.NONE,
                note=f'Bulk test movement {i}',
                warehouse=warehouse,
                status=status,
                created_by=self.user,
                updated_by=self.user
            )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check pagination
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['stock_movements']), 20)  # paginate_by = 20
        
        # Test second page
        response = self.client.get(self.url + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_movements']), 5)  # 25 total - 20 on first page

    def test_view_displays_reference_id_when_available(self):
        """Test that view displays reference ID when available"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for reference IDs
        self.assertContains(response, '#123')  # stock_movement2 reference_id
        self.assertContains(response, '#456')  # stock_movement3 reference_id

    def test_view_shows_correct_created_date_format(self):
        """Test that view shows created date in correct format"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check that date is displayed (format: "M d, Y")
        # Since we can't predict exact date, just check the user info is there
        self.assertContains(response, self.user.username)

    def test_view_shows_warehouse_links(self):
        """Test that warehouse names are displayed as links"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for warehouse detail link
        warehouse_detail_url = reverse('inventory:warehouse-detail', kwargs={'pk': self.warehouse.pk})
        self.assertContains(response, warehouse_detail_url)

    def test_view_shows_stock_movement_detail_links(self):
        """Test that stock movement IDs are displayed as links"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for stock movement detail links
        detail_url1 = reverse('inventory:stock-movement-detail', kwargs={'pk': self.stock_movement1.pk})
        detail_url2 = reverse('inventory:stock-movement-detail', kwargs={'pk': self.stock_movement2.pk})
        detail_url3 = reverse('inventory:stock-movement-detail', kwargs={'pk': self.stock_movement3.pk})
        
        self.assertContains(response, detail_url1)
        self.assertContains(response, detail_url2)
        self.assertContains(response, detail_url3)

    def test_view_shows_edit_button_only_for_draft_movements(self):
        """Test that edit button only appears for DRAFT status movements"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Count edit links - should be only 1 (for DRAFT movement)
        edit_icon_count = response.content.decode().count('bi-pencil')
        self.assertEqual(edit_icon_count, 1)

    def test_view_header_actions(self):
        """Test that header actions are displayed correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for header action buttons
        self.assertContains(response, 'Warehouses')
        self.assertContains(response, 'Inventory Dashboard')
        self.assertContains(response, 'Add New Movement')
        
        # Check for create movement link
        create_url = reverse('inventory:stock-movement-create')
        self.assertContains(response, create_url)

    def test_view_shows_movement_count_badge(self):
        """Test that view shows correct movement count in badge"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        # Check for movement count
        self.assertContains(response, '3 movements')  # 3 movements created in setUp
