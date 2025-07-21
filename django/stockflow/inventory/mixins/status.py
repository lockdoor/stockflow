"""
Status Mixin

Provides common status management functionality for models
that have active/inactive states.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.core.exceptions import ValidationError


class StatusMixin(models.Model):
    """
    Abstract mixin that provides status management functionality.
    
    Includes:
    - is_active field
    - Status management methods
    - Validation for status changes
    """
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this record is active and can be used"
    )
    
    class Meta:
        abstract = True
    
    def activate(self):
        """Activate this record"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate this record"""
        self.is_active = False
    
    def toggle_status(self):
        """Toggle active status"""
        self.is_active = not self.is_active
    
    @property
    def status_display(self):
        """Get human-readable status"""
        return "Active" if self.is_active else "Inactive"
    
    def can_deactivate(self):
        """
        Check if this record can be deactivated.
        Override in subclasses to add specific business rules.
        
        Returns:
            tuple: (can_deactivate: bool, reason: str)
        """
        return True, ""
    
    def validate_status_change(self):
        """
        Validate status changes before saving.
        Override in subclasses for specific validation rules.
        """
        if not self.is_active:
            can_deactivate, reason = self.can_deactivate()
            if not can_deactivate:
                raise ValidationError(f"Cannot deactivate: {reason}")
    
    def save(self, *args, **kwargs):
        """Save with status validation"""
        self.validate_status_change()
        super().save(*args, **kwargs)
