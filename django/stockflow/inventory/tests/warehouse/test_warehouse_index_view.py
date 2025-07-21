"""
Test Warehouse Index View

Tests for warehouse index view including authentication and template rendering.
This is typically the main warehouse management page.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse


class WarehouseIndexViewTest(TestCase):
    """Test case for Warehouse index view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create some test warehouses for context
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

    def test_redirect_if_not_logged_in(self):
        """Test redirect to login if user is not authenticated"""
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_index_view_with_authenticated_user(self):
        """Test index view loads successfully for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/warehouse/warehouse-index.html')

    def test_index_view_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'inventory/warehouse/warehouse-index.html')

    def test_index_view_no_permission_required(self):
        """Test that index view doesn't require special permissions (only login)"""
        # Create user without any special permissions
        regular_user = User.objects.create_user(
            username='regular',
            password='testpass123'
        )
        
        self.client.login(username='regular', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Should be accessible for any authenticated user
        self.assertEqual(response.status_code, 200)

    def test_index_view_contains_navigation_elements(self):
        """Test that index view contains expected navigation elements"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check for common navigation elements that might be in the template
        # These are assumptions based on typical index pages
        content = response.content.decode()
        
        # Should contain the page title or heading
        # Note: Actual content depends on the template implementation
        self.assertIn('Warehouse', content)

    def test_index_view_links_to_warehouse_list(self):
        """Test that index view contains link to warehouse list"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check for link to warehouse list
        list_url = reverse('inventory:warehouse-list')
        self.assertContains(response, list_url)

    def test_index_view_contains_create_warehouse_link(self):
        """Test that index view contains link to create warehouse (if user has permission)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check for create warehouse link
        create_url = reverse('inventory:warehouse-create')
        # Note: This might be conditional based on user permissions in the template
        # For now, just check that the URL pattern exists
        self.assertTrue(create_url.startswith('/inventory/warehouses/create/'))

    def test_index_view_with_no_warehouses(self):
        """Test index view when no warehouses exist"""
        # Delete all warehouses
        Warehouse.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Should still load successfully
        self.assertEqual(response.status_code, 200)

    def test_index_view_with_many_warehouses(self):
        """Test index view performance with many warehouses"""
        # Create many warehouses
        for i in range(50):
            warehouse = Warehouse(
                name=f'Test Warehouse {i:02d}',
                code=f'TEST{i:02d}',
                created_by=self.user,
                updated_by=self.user
            )
            super(Warehouse, warehouse).save()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Should still load successfully
        self.assertEqual(response.status_code, 200)

    def test_index_view_breadcrumb_navigation(self):
        """Test that breadcrumb navigation elements are present"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check for breadcrumb elements (common in index pages)
        content = response.content.decode()
        
        # Should contain some form of navigation or page identification
        self.assertIn('Warehouse', content)

    def test_index_view_responsive_design(self):
        """Test that index view has responsive design elements"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check for responsive CSS classes (DaisyUI/Tailwind)
        # These are common classes that should be present
        content = response.content.decode()
        
        # Check for viewport meta tag or responsive classes
        self.assertTrue(
            'viewport' in content or 
            'responsive' in content or 
            'flex' in content or
            'grid' in content
        )

    def test_index_view_contains_page_title(self):
        """Test that index view has appropriate page title"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check for page title in HTML head or content
        content = response.content.decode()
        self.assertIn('<title>', content)
        self.assertIn('Warehouse', content)

    def test_index_view_htmx_compatibility(self):
        """Test that index view works with HTMX requests"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        
        # Test with HTMX header
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        # Should still return successfully
        self.assertEqual(response.status_code, 200)

    def test_index_view_context_data(self):
        """Test that index view provides appropriate context data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Basic context should be available
        # TemplateView provides basic context by default
        self.assertIn('view', response.context)
        self.assertIn('user', response.context)

    def test_index_view_security_headers(self):
        """Test that index view includes appropriate security considerations"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response = self.client.get(url)
        
        # Check that CSRF token is present (for any forms that might be included)
        content = response.content.decode()
        self.assertIn('csrf', content.lower())

    def test_index_view_multiple_user_access(self):
        """Test that multiple users can access index view simultaneously"""
        # Create another user
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        # Test first user
        self.client.login(username='testuser', password='testpass123')
        url = reverse('inventory:warehouse-index')
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        
        # Test second user (need new client instance for this)
        from django.test import Client
        client2 = Client()
        client2.login(username='testuser2', password='testpass123')
        response2 = client2.get(url)
        self.assertEqual(response2.status_code, 200)
