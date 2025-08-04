"""
Test Category Validators

This module contains tests for the Category validator classes.
Tests cover validation logic, error handling, and business rules.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models.category import Category
from catalog.validators.category_validators import (
    CategoryNameValidator,
    CategoryBusinessRulesValidator
)


class CategoryNameValidatorTest(TestCase):
    """Test cases for CategoryNameValidator"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_valid_category_name(self):
        """Test validation with valid category name"""
        category = Category(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_empty_category_name(self):
        """Test validation with empty category name"""
        category = Category(
            name='',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('cannot be empty', str(errors[0]))
    
    def test_whitespace_only_category_name(self):
        """Test validation with whitespace-only category name"""
        category = Category(
            name='   ',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('cannot be empty', str(errors[0]))
    
    def test_category_name_too_short(self):
        """Test validation with category name too short"""
        category = Category(
            name='A',  # Only 1 character
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('at least 2 characters', str(errors[0]))
    
    def test_category_name_too_long(self):
        """Test validation with category name too long"""
        category = Category(
            name='A' * 101,  # Max length is 100
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('cannot exceed 100 characters', str(errors[0]))
    
    def test_category_name_minimum_valid_length(self):
        """Test validation with minimum valid category name length"""
        category = Category(
            name='AB',  # Exactly 2 characters
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_category_name_maximum_valid_length(self):
        """Test validation with maximum valid category name length"""
        category = Category(
            name='A' * 100,  # Exactly 100 characters
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_duplicate_category_name_new_instance(self):
        """Test validation with duplicate name for new instance"""
        # Create existing category
        Category.objects.create(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create new category with same name
        new_category = Category(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(new_category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('already exists', str(errors[0]))
    
    def test_duplicate_category_name_update_same_instance(self):
        """Test validation with same name for existing instance (should be valid)"""
        # Create existing category
        category = Category.objects.create(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update same category with same name (should be valid)
        category.note = 'Updated note'
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_case_insensitive_duplicate_detection(self):
        """Test that duplicate detection is case insensitive"""
        # Create existing category
        Category.objects.create(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create new category with different case
        new_category = Category(
            name='electronics',  # Different case
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(new_category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('already exists', str(errors[0]))


class CategoryBusinessRulesValidatorTest(TestCase):
    """Test cases for CategoryBusinessRulesValidator"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_valid_active_category(self):
        """Test validation with valid active category"""
        category = Category(
            name='Electronics',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_valid_inactive_category(self):
        """Test validation with valid inactive category"""
        category = Category(
            name='Electronics',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_category_with_special_characters_in_name(self):
        """Test validation with special characters in name"""
        category = Category(
            name='Electronics & Gadgets',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        # Should be valid - special characters allowed
        self.assertEqual(len(errors), 0)
    
    def test_category_with_numbers_in_name(self):
        """Test validation with numbers in name"""
        category = Category(
            name='Electronics 2024',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        # Should be valid - numbers allowed
        self.assertEqual(len(errors), 0)
    
    def test_category_deactivation_business_rules(self):
        """Test business rules when deactivating category"""
        # Create active category
        category = Category.objects.create(
            name='Electronics',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to deactivate
        category.is_active = False
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        # Should be valid - no items to check in test
        self.assertEqual(len(errors), 0)
    
    def test_category_reactivation_business_rules(self):
        """Test business rules when reactivating category"""
        # Create inactive category
        category = Category.objects.create(
            name='Electronics',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to reactivate
        category.is_active = True
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        # Should be valid
        self.assertEqual(len(errors), 0)
    
    def test_category_with_long_note(self):
        """Test validation with very long note"""
        category = Category(
            name='Electronics',
            note='A' * 1000,  # Very long note
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        # Should be valid - note field has no strict length limit in business rules
        self.assertEqual(len(errors), 0)


class CategoryValidatorIntegrationTest(TestCase):
    """Integration tests for Category validators"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_all_validators_with_valid_category(self):
        """Test all validators with valid category"""
        category = Category(
            name='Electronics',
            note='Electronic devices and accessories',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        validators = category.get_validators()
        all_errors = []
        
        for validator in validators:
            errors = validator.validate()
            all_errors.extend(errors)
        
        self.assertEqual(len(all_errors), 0)
    
    def test_all_validators_with_invalid_category(self):
        """Test all validators with invalid category"""
        # Create existing category first
        Category.objects.create(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate
        category = Category(
            name='Electronics',  # Duplicate name
            created_by=self.user,
            updated_by=self.user
        )
        
        validators = category.get_validators()
        all_errors = []
        
        for validator in validators:
            errors = validator.validate()
            all_errors.extend(errors)
        
        self.assertGreater(len(all_errors), 0)
    
    def test_validator_error_messages_are_helpful(self):
        """Test that validator error messages are helpful"""
        category = Category(
            name='',  # Empty name
            created_by=self.user,
            updated_by=self.user
        )
        
        validators = category.get_validators()
        all_errors = []
        
        for validator in validators:
            errors = validator.validate()
            all_errors.extend(errors)
        
        # Check that errors contain helpful messages
        error_messages = [str(error) for error in all_errors]
        self.assertTrue(any('name' in msg.lower() for msg in error_messages))
        self.assertTrue(any('empty' in msg.lower() for msg in error_messages))
