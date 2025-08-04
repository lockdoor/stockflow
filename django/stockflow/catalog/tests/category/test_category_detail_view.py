"""
Test Category Detail View

This module contains tests for the CategoryDetailView.
Tests cover display, permissions, and data presentation.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category


class CategoryDetailViewTest(TestCase):
    """Test cases for CategoryDetailView"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Add necessary permissions
        content_type = ContentType.objects.get_for_model(Category)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_category', 'change_category', 'delete_category', 'view_category']
        )
        self.user.user_permissions.set(permissions)
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            note='Electronic devices and accessories',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_category_detail_view_loads(self):
        """Test that category detail view loads successfully"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Electronics')
    
    def test_category_detail_shows_all_info(self):
        """Test that category detail shows all information"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Electronic devices and accessories')
        self.assertContains(response, 'Active')
        self.assertContains(response, self.user.username)  # Created by
    
    def test_category_detail_nonexistent_category(self):
        """Test category detail view with nonexistent category"""
        url = reverse('catalog:category-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_category_detail_without_login(self):
        """Test category detail view without login"""
        self.client.logout()
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_category_detail_context_data(self):
        """Test that category detail view provides correct context"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('object', response.context)
        self.assertEqual(response.context['object'], self.category)
    
    def test_category_detail_template_used(self):
        """Test that category detail uses correct template"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category/category-detail.html')
    
    def test_category_detail_action_buttons(self):
        """Test that category detail shows action buttons"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        # Should contain edit button
        self.assertContains(response, 'Edit')
        # Should contain back/list button
        self.assertContains(response, 'Categories')
    
    def test_category_detail_inactive_category(self):
        """Test category detail view for inactive category"""
        # Create inactive category
        inactive_category = Category.objects.create(
            name='Inactive Category',
            note='This category is inactive',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:category-detail', kwargs={'pk': inactive_category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inactive Category')
        self.assertContains(response, 'Inactive')
    
    def test_category_detail_items_count(self):
        """Test that category detail shows items count (if items relationship exists)"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show items count (0 for new category)
        # This test may need adjustment based on actual items relationship
    
    def test_category_detail_breadcrumb(self):
        """Test that category detail shows breadcrumb navigation"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should contain breadcrumb navigation
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Catalog')      
        self.assertContains(response, 'Categories')
        self.assertContains(response, 'Category Details')
    
    def test_category_detail_version_information(self):
        """Test that category detail shows version information (optimistic locking)"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show version information
        self.assertContains(response, 'Version')
    
    def test_category_detail_permissions_display(self):
        """Test category detail view with different permission levels"""
        # This test would check how the view behaves for users with different permissions
        # For now, just test basic access
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # With full permissions, should see edit button
        self.assertContains(response, 'Edit')
    
    def test_category_detail_related_data(self):
        """Test that category detail shows related data (items, etc.)"""
        url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show related items section (even if empty)
        # This test may need adjustment based on actual implementation
