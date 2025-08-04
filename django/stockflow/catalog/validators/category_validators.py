"""
Category Validators

This module contains validators for the Category model.
Implements business rules and field validation logic.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError
from common.validators.base import BaseValidator


class CategoryNameValidator(BaseValidator):
    """Validator for category name field"""
    
    def validate(self):
        """Validate category name"""
        errors = []
        
        # Check if name is provided
        if not self.instance.name or not self.instance.name.strip():
            errors.append("Category name cannot be empty.")
            return errors
        
        # Normalize name
        name = self.instance.name.strip()
        
        # Check length
        if len(name) < 2:
            errors.append("Category name must be at least 2 characters long.")
        
        if len(name) > 100:
            errors.append("Category name cannot exceed 100 characters.")
        
        # Check for duplicate name (case insensitive)
        from catalog.models.category import Category
        existing_qs = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            existing_qs = existing_qs.exclude(pk=self.instance.pk)
        
        if existing_qs.exists():
            errors.append(f"Category with name '{name}' already exists.")
        
        return errors


class CategoryBusinessRulesValidator(BaseValidator):
    """Validator for category business rules"""
    
    def validate(self):
        """Validate category business rules"""
        errors = []
        
        # If deactivating, check dependencies
        if hasattr(self.instance, '_state') and self.instance._state.adding is False:
            if not self.instance.is_active:
                can_deactivate, reason = self.instance.can_deactivate()
                if not can_deactivate:
                    errors.append(reason)
        
        return errors
