"""
Immutable Mixin

Provides immutability functionality for models based on status or other conditions.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError
from django.db import models


class ImmutableMixin(models.Model):
    """
    Mixin to provide immutability based on status or custom conditions.
    
    Models using this mixin should implement:
    - is_immutable() method to determine if the instance is immutable
    - get_immutable_reason() method to provide user-friendly error message
    """
    
    class Meta:
        abstract = True
    
    def is_immutable(self):
        """
        Override this method to define when the instance is immutable.
        Default implementation returns False (always mutable).
        """
        return False
    
    def get_immutable_reason(self):
        """
        Override this method to provide a user-friendly error message.
        """
        return "This record cannot be modified."
    
    def save(self, *args, **kwargs):
        """
        Override save to check immutability before saving.
        """
        if self.pk and self.is_immutable():
            # Allow version increment and audit fields update
            try:
                current = self.__class__.objects.get(pk=self.pk)
                self._check_immutable_fields(current)
            except self.__class__.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Override delete to check immutability before deletion.
        """
        if self.is_immutable():
            raise ValidationError(self.get_immutable_reason())
        
        super().delete(*args, **kwargs)
    
    def _check_immutable_fields(self, current_instance):
        """
        Check if any immutable fields have been changed.
        """
        # Fields that are allowed to change even when immutable
        mutable_fields = getattr(self, 'mutable_when_immutable_fields', [
            'version', 'updated_at', 'updated_by'
        ])
        
        for field in self._meta.fields:
            if field.name not in mutable_fields:
                current_value = getattr(current_instance, field.name)
                new_value = getattr(self, field.name)
                if current_value != new_value:
                    raise ValidationError(self.get_immutable_reason())


class OptimisticLockMixin(models.Model):
    """
    Mixin to provide optimistic locking functionality.
    
    Requires a 'version' field in the model.
    """
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Override save to implement optimistic locking.
        """
        if self.pk:
            try:
                current = self.__class__.objects.get(pk=self.pk)
                if current.version != self.version:
                    raise ValidationError(
                        "The record has been modified by another user. "
                        "Please refresh and try again."
                    )
                self.version += 1
            except self.__class__.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
