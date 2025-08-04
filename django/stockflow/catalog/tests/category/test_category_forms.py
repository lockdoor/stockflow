"""
Test Category Forms

This module contains tests for the Category forms.
Tests cover form validation, field handling, and save functionality.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from catalog.forms.category_form import CategoryForm
from catalog.models.category import Category


class CategoryFormTest(TestCase):
    """Test cases for CategoryForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Valid form data
        self.valid_form_data = {
            'name': 'Electronics',
            'note': 'Electronic devices and accessories',
            'is_active': True
        }
    
    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form = CategoryForm(data=self.valid_form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_save_creates_category(self):
        """Test that form save creates category correctly"""
        form = CategoryForm(data=self.valid_form_data, user=self.user)
        
        self.assertTrue(form.is_valid())
        category = form.save()
        
        self.assertEqual(category.name, 'Electronics')
        self.assertEqual(category.note, 'Electronic devices and accessories')
        self.assertTrue(category.is_active)
        self.assertEqual(category.created_by, self.user)
        self.assertEqual(category.updated_by, self.user)
    
    def test_form_without_name(self):
        """Test form validation without name"""
        data = self.valid_form_data.copy()
        data['name'] = ''
        
        form = CategoryForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_with_whitespace_name(self):
        """Test form validation with whitespace-only name"""
        data = self.valid_form_data.copy()
        data['name'] = '   '
        
        form = CategoryForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_with_long_name(self):
        """Test form validation with name too long"""
        data = self.valid_form_data.copy()
        data['name'] = 'A' * 101  # Max length is 100
        
        form = CategoryForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_without_note(self):
        """Test form validation without note (should be valid)"""
        data = self.valid_form_data.copy()
        del data['note']
        
        form = CategoryForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_without_is_active(self):
        """Test form validation without is_active (checkbox behavior)"""
        data = self.valid_form_data.copy()
        del data['is_active']
        
        form = CategoryForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        
        category = form.save()
        # Note: When checkbox is not sent in form data, Django interprets as False
        # This is normal checkbox behavior in HTML forms
        self.assertFalse(category.is_active)  # Checkbox not checked = False
    
    def test_form_with_duplicate_name(self):
        """Test form validation with duplicate name"""
        # Create existing category
        Category.objects.create(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        form = CategoryForm(data=self.valid_form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_update_existing_category(self):
        """Test updating existing category through form"""
        # Create existing category
        category = Category.objects.create(
            name='Electronics',
            note='Old note',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update data
        update_data = {
            'name': 'Electronics Updated',
            'note': 'New note',
            'is_active': True
        }
        
        form = CategoryForm(data=update_data, instance=category, user=self.user)
        self.assertTrue(form.is_valid())
        
        updated_category = form.save()
        self.assertEqual(updated_category.name, 'Electronics Updated')
        self.assertEqual(updated_category.note, 'New note')
        self.assertEqual(updated_category.updated_by, self.user)
    
    def test_form_update_with_same_name(self):
        """Test updating category with same name (should be valid)"""
        # Create existing category
        category = Category.objects.create(
            name='Electronics',
            note='Old note',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update with same name but different note
        update_data = {
            'name': 'Electronics',  # Same name
            'note': 'New note',
            'is_active': True
        }
        
        form = CategoryForm(data=update_data, instance=category, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_deactivate_category(self):
        """Test deactivating category through form"""
        # Create active category
        category = Category.objects.create(
            name='Electronics',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Deactivate
        update_data = {
            'name': 'Electronics',
            'note': '',
            'is_active': False
        }
        
        form = CategoryForm(data=update_data, instance=category, user=self.user)
        self.assertTrue(form.is_valid())
        
        updated_category = form.save()
        self.assertFalse(updated_category.is_active)
    
    def test_form_fields_rendered(self):
        """Test that form renders expected fields"""
        form = CategoryForm(user=self.user)
        
        # Check that expected fields are present
        expected_fields = ['name', 'note', 'is_active']
        for field_name in expected_fields:
            self.assertIn(field_name, form.fields)
    
    def test_form_field_attributes(self):
        """Test form field attributes"""
        form = CategoryForm(user=self.user)
        
        # Test name field
        name_field = form.fields['name']
        self.assertTrue(name_field.required)
        self.assertEqual(name_field.max_length, 100)
        
        # Test note field
        note_field = form.fields['note']
        self.assertFalse(note_field.required)
        
        # Test is_active field
        is_active_field = form.fields['is_active']
        self.assertFalse(is_active_field.required)  # Should have default
    
    def test_form_without_user_parameter(self):
        """Test form behavior when user parameter is not provided"""
        # This should still work but won't set audit fields automatically
        form = CategoryForm(data=self.valid_form_data)
        
        # Form should still validate
        self.assertTrue(form.is_valid())
        
        # But save might fail without proper audit fields
        # (depends on form implementation)
