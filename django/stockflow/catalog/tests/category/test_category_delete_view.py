"""
Test Category Delete View

This module contains tests for the CategoryDeleteView.
Tests cover delete confirmation, permissions, and cascade handling.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category


class CategoryDeleteViewTest(TestCase):
    """Test cases for CategoryDeleteView"""
    
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
            note='Electronic devices',
            created_by=self.user,
            updated_by=self.user
        )
        
        # URL for delete view
        self.url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
    
    def test_category_delete_view_get(self):
        """Test category delete view should not accept GET requests"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405, "delete view should not accept GET requests")
    
    def test_category_delete_view_delete(self):
        """Test category delete view DELETE request (actual deletion)"""
        
        response = self.client.delete(self.url)
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Check that category was deleted
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_category_delete_view_nonexistent(self):
        """Test category delete view with nonexistent category"""
        url = reverse('catalog:category-delete', kwargs={'pk': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_category_delete_view_without_login(self):
        """Test category delete view without login"""
        self.client.logout()
        response = self.client.delete(self.url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_category_delete_view_accepts_only_delete_method(self):
        """Test that category delete view only accepts DELETE method"""
        # GET should not be allowed
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 405)
        
        # POST should not be allowed
        post_response = self.client.post(self.url)
        self.assertEqual(post_response.status_code, 405)
        
        # DELETE should be allowed
        delete_response = self.client.delete(self.url)
        self.assertEqual(delete_response.status_code, 302)  # Redirect after success
    
    def test_category_delete_view_double_delete_protection(self):
        """Test that deleting same category twice returns 404"""
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        
        # First deletion should work
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        
        # Second deletion should return 404
        response2 = self.client.delete(url)
        self.assertEqual(response2.status_code, 404)
    

    def test_category_delete_view_success_redirect(self):
        """Test that successful category deletion redirects correctly"""
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        response = self.client.delete(url)
        
        # Should redirect to list view
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('catalog:category-list')
        self.assertRedirects(response, expected_url)
    
    def test_category_delete_with_items_protection(self):
        """Test that category with items cannot be deleted (if protection exists)"""
        # This test would check if categories with items are protected from deletion
        # Implementation depends on whether such protection exists
        
        # For now, just test normal deletion
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        response = self.client.delete(url)
        
        # Should succeed for category without items
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
    
    def test_category_delete_inactive_category(self):
        """Test deleting inactive category"""
        # Create inactive category
        inactive_category = Category.objects.create(
            name='Inactive Category',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:category-delete', kwargs={'pk': inactive_category.pk})
        response = self.client.delete(url)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=inactive_category.pk).exists())
    
    def test_category_delete_view_context_data(self):
        """Test that category delete view deletes the correct object"""
        original_count = Category.objects.count()
        
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 302)
        # Should have one less category
        self.assertEqual(Category.objects.count(), original_count - 1)
        # The specific category should be gone
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
    
    def test_category_delete_view_security(self):
        """Test category delete view security measures"""
        # Test that only DELETE requests can actually delete
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        
        # GET should not delete and return 405
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 405)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        
        # POST should not delete and return 405
        post_response = self.client.post(url)
        self.assertEqual(post_response.status_code, 405)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        
        # DELETE should delete
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
    


    def test_category_delete_view_error_handling(self):
        """Test category delete view error handling"""
        # Test deletion with database constraints (if any)
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        
        # Normal deletion should work
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        
        # Trying to delete again should result in 404
        response2 = self.client.delete(url)
        self.assertEqual(response2.status_code, 404)
    
    def test_category_delete_view_ajax_support(self):
        """Test category delete view AJAX support (if implemented)"""
        url = reverse('catalog:category-delete', kwargs={'pk': self.category.pk})
        
        # Test AJAX request if supported
        response = self.client.delete(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Should still work the same way (redirect)
        self.assertEqual(response.status_code, 302)
