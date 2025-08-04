"""
Test Category Create View

This module contains tests for the CategoryCreateView.
Tests cover form handling, validation, permissions, and category creation.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category


class CategoryCreateViewTest(TestCase):
    """Test cases for CategoryCreateView"""
    
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
    
    def test_category_create_view_get(self):
        """Test category create view GET request"""
        url = reverse('catalog:category-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Category')
        self.assertContains(response, 'name')
        self.assertContains(response, 'note')
        self.assertContains(response, 'is_active')
    
    def test_category_create_view_post_valid(self):
        """Test category create view POST with valid data"""
        url = reverse('catalog:category-create')
        data = {
            'name': 'New Category',
            'note': 'A new category for testing',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check that category was created
        self.assertTrue(Category.objects.filter(name='New Category').exists())
        
        created_category = Category.objects.get(name='New Category')
        self.assertEqual(created_category.note, 'A new category for testing')
        self.assertEqual(created_category.created_by, self.user)
        self.assertEqual(created_category.updated_by, self.user)
    
    def test_category_create_view_post_invalid(self):
        """Test category create view POST with invalid data"""
        url = reverse('catalog:category-create')
        data = {
            'name': '',  # Empty name
            'note': 'A new category for testing',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        
        # Check that category was not created
        self.assertFalse(Category.objects.filter(note='A new category for testing').exists())
    
    def test_category_create_view_duplicate_name(self):
        """Test category create view with duplicate name"""
        # Create existing category
        Category.objects.create(
            name='Existing Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('catalog:category-create')
        data = {
            'name': 'Existing Category',  # Duplicate name
            'note': 'Another category',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
    
    def test_category_create_view_whitespace_name(self):
        """Test category create view with whitespace-only name"""
        url = reverse('catalog:category-create')
        data = {
            'name': '   ',  # Whitespace only
            'note': 'A category with whitespace name',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        # Should show validation error
        self.assertContains(response, 'This field is required')
    
    def test_category_create_view_long_name(self):
        """Test category create view with name too long"""
        url = reverse('catalog:category-create')
        data = {
            'name': 'A' * 101,  # Too long
            'note': 'A category with long name',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should stay on same page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100 characters')
    
    def test_category_create_view_without_login(self):
        """Test category create view without login"""
        self.client.logout()
        url = reverse('catalog:category-create')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_category_create_view_template_used(self):
        """Test that category create uses correct template"""
        url = reverse('catalog:category-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category/category-form.html')
    
    def test_category_create_view_form_fields(self):
        """Test that category create form has all expected fields"""
        url = reverse('catalog:category-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check for form fields
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="note"')
        self.assertContains(response, 'name="is_active"')
    
    def test_category_create_view_cancel_action(self):
        """Test category create view cancel button"""
        url = reverse('catalog:category-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should have cancel button that goes back to list
        self.assertContains(response, 'Cancel')
    
    def test_category_create_sets_audit_fields(self):
        """Test that creating category sets audit fields correctly"""
        url = reverse('catalog:category-create')
        data = {
            'name': 'Audit Test Category',
            'note': 'For testing audit fields',
            'is_active': True
        }
        
        self.client.post(url, data)
        
        category = Category.objects.get(name='Audit Test Category')
        self.assertEqual(category.created_by, self.user)
        self.assertEqual(category.updated_by, self.user)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)
        self.assertEqual(category.version, 1)  # Initial version
    
    def test_category_create_view_success_redirect(self):
        """Test that successful category creation redirects correctly"""
        url = reverse('catalog:category-create')
        data = {
            'name': 'Redirect Test Category',
            'note': 'For testing redirect',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to list view (based on view implementation)
        self.assertEqual(response.status_code, 302)
        
        # Check redirect location - view redirects to category-list
        expected_url = reverse('catalog:category-list')
        self.assertRedirects(response, expected_url)
    
    def test_category_create_view_form_validation_messages(self):
        """Test that category create view shows proper validation messages"""
        url = reverse('catalog:category-create')
        data = {
            'name': '',  # Empty name
            'note': 'Valid note',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        # Should show required field validation message
        self.assertContains(response, 'This field is required')
    
    def test_category_create_view_preserves_form_data(self):
        """Test that form data is preserved on validation errors"""
        url = reverse('catalog:category-create')
        data = {
            'name': '',  # Invalid
            'note': 'This note should be preserved',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        # Should preserve the valid note field
        self.assertContains(response, 'This note should be preserved')
