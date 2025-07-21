"""
Immutable Mixin

Provides immutable functionality for models that need to become
read-only after reaching certain status.

Author: StockFlow Team  
Created: 2025
"""

from django.core.exceptions import ValidationError


class ImmutableMixin:
    """
    Mixin to make model instances immutable based on status or condition.
    
    Models using this mixin should implement:
    - is_immutable() method that returns True if instance should be immutable
    """
    
    def is_immutable(self):
        """
        Override this method to define when instance becomes immutable.
        Default implementation returns False (always mutable).
        """
        return False
    
    def save(self, *args, **kwargs):
        """Override save to prevent updates to immutable instances"""
        if self.pk and self.is_immutable():
            # Check if this is actually an update (not just a save of existing data)
            try:
                current = self.__class__.objects.get(pk=self.pk)
                if self._has_changes(current):
                    raise ValidationError(
                        f"{self.__class__.__name__} instance (ID: {self.pk}) is immutable and cannot be updated"
                    )
            except self.__class__.DoesNotExist:
                # Record doesn't exist anymore, allow save
                pass
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion of immutable instances"""
        if self.is_immutable():
            raise ValidationError(
                f"{self.__class__.__name__} instance (ID: {self.pk}) is immutable and cannot be deleted"
            )
        
        super().delete(*args, **kwargs)
    
    def _has_changes(self, current_instance):
        """
        Check if current instance has changes compared to database version.
        Override this method for custom change detection.
        """
        # Default implementation: check all fields except auto fields
        exclude_fields = ['id', 'created_at', 'updated_at']
        
        for field in self._meta.fields:
            if field.name in exclude_fields:
                continue
                
            current_value = getattr(current_instance, field.name)
            new_value = getattr(self, field.name)
            
            if current_value != new_value:
                return True
        
        return False


class StatusImmutableMixin(ImmutableMixin):
    """
    Mixin for models that become immutable when reaching specific status values.
    
    Models using this mixin should have:
    - status field
    - IMMUTABLE_STATUSES class attribute listing immutable status values
    """
    
    IMMUTABLE_STATUSES = []
    
    def is_immutable(self):
        """Instance is immutable if status is in IMMUTABLE_STATUSES"""
        if not hasattr(self, 'status'):
            return False
        
        return self.status in self.IMMUTABLE_STATUSES


class VersionedImmutableMixin(ImmutableMixin):
    """
    Mixin that combines immutable functionality with optimistic locking.
    
    Models using this mixin should have:
    - version field (PositiveIntegerField)
    """
    
    def save(self, *args, **kwargs):
        """Override save to implement optimistic locking with version field"""
        if self.pk:
            try:
                current = self.__class__.objects.get(pk=self.pk)
                
                # Check optimistic locking before immutability check
                if hasattr(self, 'version') and hasattr(current, 'version'):
                    if current.version != self.version:
                        raise ValidationError(
                            "Record has been modified by another user. Please refresh and try again."
                        )
                
                # Check immutability
                if self.is_immutable() and self._has_changes(current):
                    raise ValidationError(
                        f"{self.__class__.__name__} instance (ID: {self.pk}) is immutable and cannot be updated"
                    )
                
                # Increment version for updates
                if hasattr(self, 'version'):
                    self.version = current.version + 1
                    
            except self.__class__.DoesNotExist:
                # Record doesn't exist anymore, allow save
                pass
        else:
            # New instance, set initial version
            if hasattr(self, 'version') and self.version is None:
                self.version = 1
        
        # Call parent save (avoiding double validation)  
        super().save(*args, **kwargs)
