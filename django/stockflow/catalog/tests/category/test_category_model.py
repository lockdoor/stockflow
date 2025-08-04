"""
Test Category Model

This module contains tests for the refactored Category model.
Tests cover validation, mixins functionality, and business rules.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from catalog.models.category import Category


class CategoryModelTest(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Sample category data
        self.valid_category_data = {
            'name': 'Electronics',
            'note': 'Electronic devices and accessories',
            'created_by': self.user,
            'updated_by': self.user
        }
    
    def test_create_category_with_valid_data(self):
        """Test creating category with valid data"""
        category = Category.objects.create(**self.valid_category_data)
        
        self.assertEqual(category.name, 'Electronics')
        self.assertEqual(category.note, 'Electronic devices and accessories')
        self.assertTrue(category.is_active)  # Default from StatusMixin
        self.assertEqual(category.created_by, self.user)
        self.assertEqual(category.updated_by, self.user)
        self.assertEqual(category.version, 1)  # Default from AuditableMixin
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)
    
    def test_category_string_representation(self):
        """Test category __str__ method"""
        category = Category.objects.create(**self.valid_category_data)
        self.assertEqual(str(category), 'Electronics')
    
    def test_category_name_normalization(self):
        """Test that category name is normalized (trimmed)"""
        data = self.valid_category_data.copy()
        data['name'] = '  Trimmed Name  '
        
        category = Category.objects.create(**data)
        self.assertEqual(category.name, 'Trimmed Name')
    
    def test_category_unique_name_constraint(self):
        """Test that category names must be unique"""
        Category.objects.create(**self.valid_category_data)
        
        # Try to create another category with same name
        with self.assertRaises(ValidationError):
            duplicate_data = self.valid_category_data.copy()
            Category(**duplicate_data).save()
    
    def test_category_name_validation_empty(self):
        """Test validation for empty category name"""
        data = self.valid_category_data.copy()
        data['name'] = ''
        
        category = Category(**data)
        with self.assertRaises(ValidationError):
            category.full_clean()
    
    def test_category_name_validation_whitespace_only(self):
        """Test validation for whitespace-only category name"""
        data = self.valid_category_data.copy()
        data['name'] = '   '
        
        with self.assertRaises(ValidationError):
            Category(**data).save()
    
    def test_category_name_validation_too_long(self):
        """Test validation for category name that's too long"""
        data = self.valid_category_data.copy()
        data['name'] = 'A' * 101  # Max length is 100
        
        category = Category(**data)
        with self.assertRaises(ValidationError):
            category.full_clean()
    
    def test_category_name_validation_duplicate(self):
        """Test validation for duplicate category name"""
        Category.objects.create(**self.valid_category_data)
        
        # Try to create another with same name
        data = self.valid_category_data.copy()
        category = Category(**data)
        
        with self.assertRaises(ValidationError):
            category.full_clean()
    
    def test_category_optional_note_field(self):
        """Test that note field is optional"""
        data = self.valid_category_data.copy()
        del data['note']
        
        category = Category.objects.create(**data)
        self.assertEqual(category.note, '')  # Default empty string
    
    def test_get_active_categories(self):
        """Test get_active class method"""
        # Create active category
        active_category = Category.objects.create(**self.valid_category_data)
        
        # Create inactive category
        inactive_data = self.valid_category_data.copy()
        inactive_data['name'] = 'Inactive Category'
        inactive_category = Category.objects.create(**inactive_data)
        
        # Deactivate the second category after creation
        inactive_category.is_active = False
        inactive_category.save()
        
        active_categories = Category.get_active()
        
        self.assertIn(active_category, active_categories)
        self.assertNotIn(inactive_category, active_categories)
        self.assertEqual(active_categories.count(), 1)
    
    def test_get_display_name(self):
        """Test get_display_name method"""
        category = Category.objects.create(**self.valid_category_data)
        self.assertEqual(category.get_display_name(), 'Electronics')
    
    def test_can_deactivate_without_items(self):
        """Test can_deactivate when category has no items"""
        category = Category.objects.create(**self.valid_category_data)
        
        can_deactivate, reason = category.can_deactivate()
        self.assertTrue(can_deactivate)
        self.assertEqual(reason, "")
    
    def test_has_items_property_without_items(self):
        """Test has_items property when category has no items"""
        category = Category.objects.create(**self.valid_category_data)
        self.assertFalse(category.has_items)
    
    def test_items_count_property_without_items(self):
        """Test items_count property when category has no items"""
        category = Category.objects.create(**self.valid_category_data)
        self.assertEqual(category.items_count, 0)
    
    def test_optimistic_locking_version_increment(self):
        """Test that version increments on update (optimistic locking)"""
        category = Category.objects.create(**self.valid_category_data)
        initial_version = category.version
        
        category.note = 'Updated note'
        category.save()
        
        self.assertEqual(category.version, initial_version + 1)
    
    def test_auditable_fields_set_on_creation(self):
        """Test that auditable fields are set correctly on creation"""
        category = Category.objects.create(**self.valid_category_data)
        
        self.assertEqual(category.created_by, self.user)
        self.assertEqual(category.updated_by, self.user)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)
    
    def test_status_mixin_functionality(self):
        """Test status mixin functionality"""
        category = Category.objects.create(**self.valid_category_data)
        
        # Should be active by default
        self.assertTrue(category.is_active)
        
        # Test deactivation
        category.is_active = False
        category.save()
        self.assertFalse(category.is_active)
    
    def test_validators_are_returned(self):
        """Test that get_validators returns validator instances"""
        category = Category(**self.valid_category_data)
        validators = category.get_validators()
        
        self.assertEqual(len(validators), 2)
        self.assertTrue(all(hasattr(v, 'validate') for v in validators))


class CategoryValidatorsTest(TestCase):
    """Test cases for Category validators"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_category_name_validator_valid_name(self):
        """Test CategoryNameValidator with valid name"""
        from catalog.validators.category_validators import CategoryNameValidator
        
        category = Category(
            name='Valid Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertEqual(len(errors), 0)
    
    def test_category_name_validator_empty_name(self):
        """Test CategoryNameValidator with empty name"""
        from catalog.validators.category_validators import CategoryNameValidator
        
        category = Category(
            name='',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('cannot be empty', str(errors[0]))
    
    def test_category_name_validator_too_short(self):
        """Test CategoryNameValidator with name too short"""
        from catalog.validators.category_validators import CategoryNameValidator
        
        category = Category(
            name='A',  # Only 1 character
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryNameValidator(category)
        errors = validator.validate()
        
        self.assertGreater(len(errors), 0)
        self.assertIn('at least 2 characters', str(errors[0]))
    
    def test_category_business_rules_validator(self):
        """Test CategoryBusinessRulesValidator"""
        from catalog.validators.category_validators import CategoryBusinessRulesValidator
        
        category = Category(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        validator = CategoryBusinessRulesValidator(category)
        errors = validator.validate()
        
        # Should pass for new active category
        self.assertEqual(len(errors), 0)
