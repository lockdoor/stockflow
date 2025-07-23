"""
OptimisticLockMixin Mixin

Provides optimistic locking functionality for models.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError
from django.db import models

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
