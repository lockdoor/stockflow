"""
Test Category Update View

This module contains tests for the CategoryUpdateView.
Tests cover form handling, validation, permissions, and category updates.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category


class CategoryUpdateViewTest(TestCase):
    """Test cases for CategoryUpdateView"""
    
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
        
        self.url = reverse('catalog:category-edit', kwargs={'pk': self.category.pk})
    
    def test_category_update_view_get(self):
        """Test category update view GET request"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update Category')
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Electronic devices')
    
    def test_category_update_view_post_valid(self):
        """Test category update view POST with valid data"""
        data = {
            'name': 'Updated Electronics',
            'note': 'Updated electronic devices',
            'is_active': True
        }
        
        response = self.client.post(self.url, data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that category was updated
        updated_category = Category.objects.get(pk=self.category.pk)
        self.assertEqual(updated_category.name, 'Updated Electronics')
        self.assertEqual(updated_category.note, 'Updated electronic devices')
        self.assertEqual(updated_category.updated_by, self.user)
        self.assertGreater(updated_category.version, 1)  # Version should increment
    
    def test_category_update_view_post_invalid(self):
        """Test category update view POST with invalid data"""
        data = {
            'name': '',  # Empty name
            'note': 'Updated electronic devices',
            'is_active': True
        }
        
        response = self.client.post(self.url, data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        
        # Check that category was not updated
        category = Category.objects.get(pk=self.category.pk)
        self.assertEqual(category.name, 'Electronics')  # Original name
    
    def test_category_update_view_same_name(self):
        """Test category update with same name (should be valid)"""
        data = {
            'name': 'Electronics',  # Same name
            'note': 'Updated note only',
            'is_active': True
        }
        
        response = self.client.post(self.url, data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        updated_category = Category.objects.get(pk=self.category.pk)
        self.assertEqual(updated_category.name, 'Electronics')
        self.assertEqual(updated_category.note, 'Updated note only')
    
    def test_category_update_view_duplicate_name(self):
        """Test category update with duplicate name"""
        # Create another category
        other_category = Category.objects.create(
            name='Other Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        data = {
            'name': 'Other Category',  # Duplicate name
            'note': 'Updated note',
            'is_active': True
        }
        
        response = self.client.post(self.url, data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
    
    def test_category_update_view_deactivate(self):
        """Test deactivating category through update view"""
        data = {
            'name': 'Electronics',
            'note': 'Electronic devices',
            'is_active': False  # Deactivate
        }
        
        response = self.client.post(self.url, data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        updated_category = Category.objects.get(pk=self.category.pk)
        self.assertFalse(updated_category.is_active)
    
    def test_category_update_view_nonexistent(self):
        """Test category update view with nonexistent category"""
        url = reverse('catalog:category-edit', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_category_update_view_without_login(self):
        """Test category update view without login"""
        self.client.logout()
        response = self.client.get(self.url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_category_update_view_template_used(self):
        """Test that category update uses correct template"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category/category-form.html')
    
    def test_category_update_view_form_prefilled(self):
        """Test that update form is prefilled with existing data"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Form should be prefilled with existing values
        self.assertContains(response, 'value="Electronics"')
        self.assertContains(response, 'Electronic devices')
    
    def test_category_update_view_cancel_action(self):
        """Test category update view cancel button"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Should have cancel button
        self.assertContains(response, 'Cancel')
    
    def test_category_update_sets_audit_fields(self):
        """Test that updating category sets audit fields correctly"""
        original_created_by = self.category.created_by
        original_created_at = self.category.created_at
        
        data = {
            'name': 'Updated for Audit',
            'note': 'Updated note',
            'is_active': True
        }
        
        self.client.post(self.url, data)
        
        category = Category.objects.get(pk=self.category.pk)
        # Created fields should remain unchanged
        self.assertEqual(category.created_by, original_created_by)
        self.assertEqual(category.created_at, original_created_at)
        # Updated fields should change
        self.assertEqual(category.updated_by, self.user)
        self.assertGreater(category.version, 1)  # Version should increment
    
    def test_category_update_view_success_redirect(self):
        """Test that successful category update redirects correctly"""
        data = {
            'name': 'Redirect Test',
            'note': 'For testing redirect',
            'is_active': True
        }
        
        response = self.client.post(self.url, data)
        
        # Should redirect to detail view
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('catalog:category-detail', kwargs={'pk': self.category.pk})
        self.assertRedirects(response, expected_url)
    
    def test_category_update_view_optimistic_locking(self):
        """Test optimistic locking behavior on concurrent updates"""
        # This test would simulate concurrent updates
        # For now, just test version increment
        original_version = self.category.version
        
        data = {
            'name': 'Version Test',
            'note': 'Testing version increment',
            'is_active': True
        }
        
        self.client.post(self.url, data)
        
        updated_category = Category.objects.get(pk=self.category.pk)
        self.assertEqual(updated_category.version, original_version + 1)
    
    def test_category_update_view_preserves_form_data(self):
        """Test that form data is preserved on validation errors"""
        data = {
            'name': '',  # Invalid
            'note': 'This note should be preserved',
            'is_active': True
        }
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, 200)
        # Should preserve the valid note field
        self.assertContains(response, 'This note should be preserved')
