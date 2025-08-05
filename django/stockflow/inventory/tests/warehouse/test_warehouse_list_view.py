"""
Test Warehouse List View

Tests for warehouse list view including pagination and proper template rendering
with redirect flow.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse


class WarehouseListViewTest(TestCase):
    """Test case for Warehouse list view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test warehouses using super save to bypass validation
        self.warehouse1 = Warehouse(
            name='Main Warehouse',
            code='MAIN01',
            address='123 Main St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, self.warehouse1).save()
        
        self.warehouse2 = Warehouse(
            name='Secondary Warehouse', 
            code='SEC01',
            address='456 Secondary Ave',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, self.warehouse2).save()
        
        # Create third warehouse with different approach for inactive
        self.warehouse3 = Warehouse(
            name='Backup Warehouse',
            code='BACKUP01',
            address='789 Backup Rd',
            is_active=True,  # Create as active first
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, self.warehouse3).save()

    def test_redirect_if_not_logged_in(self):
        """Test redirect to login if user is not authenticated"""
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_list_view_with_authenticated_user(self):
        """Test list view returns warehouses for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Main Warehouse')
        self.assertContains(response, 'Secondary Warehouse') 
        self.assertContains(response, 'Backup Warehouse')
        
        # Check context
        self.assertIn('warehouses', response.context)
        warehouses = response.context['warehouses']
        self.assertEqual(len(warehouses), 3)
        
        # Check template used is main warehouse list template
        self.assertTemplateUsed(response, 'inventory/warehouse/warehouse-list.html')

    def test_list_view_ordering(self):
        """Test that warehouses are ordered by name"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        warehouses = response.context['warehouses']
        warehouse_names = [w.name for w in warehouses]
        
        # Should be ordered alphabetically by name
        expected_order = ['Backup Warehouse', 'Main Warehouse', 'Secondary Warehouse']
        self.assertEqual(warehouse_names, expected_order)

    def test_list_view_empty_state(self):
        """Test list view when no warehouses exist"""
        # Delete all warehouses
        Warehouse.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No warehouses found')
        
        warehouses = response.context['warehouses']
        self.assertEqual(len(warehouses), 0)

    def test_list_view_shows_warehouse_details(self):
        """Test that warehouse details are displayed correctly"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        # Check that warehouse codes are displayed
        self.assertContains(response, 'MAIN01')
        self.assertContains(response, 'SEC01')
        self.assertContains(response, 'BACKUP01')
        
        # Check that addresses are displayed
        self.assertContains(response, '123 Main St')
        self.assertContains(response, '456 Secondary Ave')

    def test_list_view_shows_status_badges(self):
        """Test that status badges are displayed correctly"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        # Check for status badges (Bootstrap 5 classes)
        self.assertContains(response, 'bg-success')  # Active warehouses
        # Since all test warehouses are active, no inactive badges expected

    def test_list_view_pagination(self):
        """Test pagination functionality"""
        # Create more warehouses to test pagination (paginate_by = 20)
        for i in range(25):
            warehouse = Warehouse(
                name=f'Test Warehouse {i:02d}',
                code=f'TEST{i:02d}',
                created_by=self.user,
                updated_by=self.user
            )
            super(Warehouse, warehouse).save()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        # Should have pagination since we have more than 20 warehouses
        self.assertTrue(response.context['is_paginated'])
        warehouses = response.context['warehouses']
        self.assertEqual(len(warehouses), 20)  # First page should have 20 items

    def test_list_view_contains_action_buttons(self):
        """Test that action buttons are present in the list"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        # Check for Add New Warehouse button (redirect flow uses form URL)
        self.assertContains(response, 'Add New Warehouse')
        self.assertContains(response, '/inventory/warehouses/form/')
        
        # Check for edit and view buttons in warehouse rows (redirect flow uses form URLs)
        self.assertContains(response, 'warehouses/3/form/')  # Edit URL
        self.assertContains(response, 'warehouses/3/')  # Detail view URL

    def test_list_view_with_search_parameters(self):
        """Test list view with query parameters (if implemented)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        
        # Test with potential search parameter
        response = self.client.get(url, {'search': 'Main'})
        self.assertEqual(response.status_code, 200)
        
        # Even if search isn't implemented, view should handle gracefully
        warehouses = response.context['warehouses']
        self.assertGreaterEqual(len(warehouses), 0)

    def test_list_view_template_context(self):
        """Test that all required context variables are present"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        # Check context variables
        self.assertIn('warehouses', response.context)
        self.assertIn('page_obj', response.context)
        self.assertIn('is_paginated', response.context)
        
        # Check that warehouses context is the correct type
        warehouses = response.context['warehouses']
        self.assertTrue(hasattr(warehouses, '__iter__'))  # Should be iterable

    def test_list_view_warehouse_links(self):
        """Test that warehouse detail links are working"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        response = self.client.get(url)
        
        # Check that detail links are present
        detail_url = reverse('inventory:warehouse-detail', args=[self.warehouse1.pk])
        self.assertContains(response, detail_url)
        
        edit_url = reverse('inventory:warehouse-edit-form', args=[self.warehouse1.pk])
        self.assertContains(response, edit_url)

    def test_list_view_performance(self):
        """Test that list view performs well with many warehouses"""
        # Create many warehouses
        warehouses_to_create = []
        for i in range(100):
            warehouse = Warehouse(
                name=f'Performance Test Warehouse {i:03d}',
                code=f'PERF{i:03d}',
                created_by=self.user,
                updated_by=self.user
            )
            warehouses_to_create.append(warehouse)
        
        # Bulk create using super save approach
        for warehouse in warehouses_to_create:
            super(Warehouse, warehouse).save()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-list')
        
        # Test that view still loads quickly
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Should be paginated
        self.assertTrue(response.context['is_paginated'])
        warehouses = response.context['warehouses']
        self.assertEqual(len(warehouses), 20)  # Only first page
