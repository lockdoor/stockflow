"""
Test Category List View

This module contains tests for the CategoryListView.
Tests cover display, ordering, permissions, and filtering.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category


class CategoryListViewTest(TestCase):
    """Test cases for CategoryListView"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Create test categories
        self.category1 = Category.objects.create(
            name='Electronics',
            note='Electronic devices',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.category2 = Category.objects.create(
            name='Books',
            note='Books and publications',
            is_active=False,  # Inactive category
            created_by=self.user,
            updated_by=self.user
        )
        
        self.category3 = Category.objects.create(
            name='Accessories',  # Should come first alphabetically
            note='Various accessories',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_category_list_view_loads(self):
        """Test that category list view loads successfully"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Categories')
    
    def test_category_list_shows_all_categories(self):
        """Test that category list shows all categories"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Books')
        self.assertContains(response, 'Accessories')
    
    def test_category_list_ordering(self):
        """Test that category list is ordered by name"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        content = response.content.decode()
        accessories_pos = content.find('Accessories')
        books_pos = content.find('Books')
        electronics_pos = content.find('Electronics')
        
        # Should be in alphabetical order
        self.assertLess(accessories_pos, books_pos)
        self.assertLess(books_pos, electronics_pos)
    
    def test_category_list_shows_status(self):
        """Test that category list shows active/inactive status"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        # Should show active status
        self.assertContains(response, 'Active')
        # Should show inactive status
        self.assertContains(response, 'Inactive')
    
    def test_category_list_shows_notes(self):
        """Test that category list shows category notes or placeholder"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        # Test that description column exists
        self.assertContains(response, '<th>Description</th>')
        # Categories without notes should show placeholder
        self.assertContains(response, 'No description')
    
    def test_category_list_without_login(self):
        """Test category list view without login"""
        self.client.logout()
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_category_list_context_data(self):
        """Test that category list view provides correct context"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('object_list', response.context)
        self.assertEqual(len(response.context['object_list']), 3)
    
    def test_category_list_template_used(self):
        """Test that category list uses correct template"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category/category-list.html')
    
    def test_category_list_action_buttons(self):
        """Test that category list shows action buttons"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        # Should contain create button (actual text is "Add Category")
        self.assertContains(response, 'Add Category')
        # Should contain action buttons
        self.assertContains(response, 'btn-group')
        # Should contain view/edit/delete icons
        self.assertContains(response, 'bi-eye')
        self.assertContains(response, 'bi-pencil-square')
    
    def test_category_list_pagination(self):
        """Test category list pagination (if implemented)"""
        # Create many categories to test pagination
        for i in range(50):
            Category.objects.create(
                name=f'Category {i:02d}',
                created_by=self.user,
                updated_by=self.user
            )
        
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # If pagination is implemented, check for pagination controls
        # This will depend on your pagination settings
    
    def test_category_list_empty_state(self):
        """Test category list when no categories exist"""
        # Delete all categories
        Category.objects.all().delete()
        
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show empty message or handle empty state gracefully
        self.assertContains(response, 'Categories')  # At least the title should be there
    
    def test_category_list_search_functionality(self):
        """Test category list search (if implemented)"""
        url = reverse('catalog:category-list')
        
        # Test search parameter if implemented
        response = self.client.get(url, {'search': 'Electronics'})
        self.assertEqual(response.status_code, 200)
        
        # If search is implemented, it should filter results
        # This test may need to be adjusted based on actual implementation
    
    def test_category_list_filter_by_status(self):
        """Test category list filtering by status (if implemented)"""
        url = reverse('catalog:category-list')
        
        # Test filtering by active status
        response = self.client.get(url, {'status': 'active'})
        self.assertEqual(response.status_code, 200)
        
        # Test filtering by inactive status
        response = self.client.get(url, {'status': 'inactive'})
        self.assertEqual(response.status_code, 200)
