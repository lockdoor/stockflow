"""
Category Model

This module defines the Category model using mixins for clean separation of concerns.
Uses AuditableMixin for audit fields and optimistic locking,
StatusMixin for status management, and ValidatableMixin for validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from common.mixins.auditable import AuditableMixin
from common.mixins.status import StatusMixin
from common.mixins.validatable import ValidatableMixin
from catalog.validators.category_validators import (
    CategoryNameValidator,
    CategoryBusinessRulesValidator
)

class Category(AuditableMixin, StatusMixin, ValidatableMixin, models.Model):
    """
    Category model for catalog management.
    
    Represents product categories for organizing inventory items.
    Includes name, note and status management.
    """
    
    # Core fields
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Category display name"
    )
    note = models.TextField(
        blank=True, 
        default='',
        help_text="Optional note about the category"
    )

    class Meta:
        ordering = ['name']
        db_table = 'catalog_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        """String representation of the category"""
        return self.name

    def get_validators(self):
        """Return list of validators for this category"""
        return [
            CategoryNameValidator(self),
            CategoryBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """Save with validation and name normalization"""
        # Normalize name
        if self.name:
            self.name = self.name.strip()
            
        # Validate empty name after trimming
        if not self.name:
            from django.core.exceptions import ValidationError
            raise ValidationError({'name': 'Category name cannot be empty or whitespace only.'})
        
        # Run validation through mixins
        self.full_clean()
        
        # Call parent save (includes optimistic locking and status validation)
        super().save(*args, **kwargs)

    def can_deactivate(self):
        """Check if category can be deactivated"""
        # Skip validation if instance doesn't have a primary key yet (during creation)
        if not self.pk:
            return True, ""
            
        # Check for items using this category
        if self.has_items:
            return False, "Category has items assigned to it"
        
        return True, ""

    @classmethod
    def get_active(cls):
        """Get all active categories"""
        return cls.objects.filter(is_active=True)

    def get_display_name(self):
        """Get formatted display name"""
        return self.name

    @property
    def has_items(self):
        """Check if category has any items"""
        return hasattr(self, 'items') and self.items.exists()
    
    @property
    def items_count(self):
        """Get count of items in this category"""
        return self.items.count() if hasattr(self, 'items') else 0
