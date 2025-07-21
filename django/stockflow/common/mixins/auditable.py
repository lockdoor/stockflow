"""
Audit Mixin

Provides common audit fields and optimistic locking functionality
for all inventory models.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


class AuditableMixin(models.Model):
    """
    Abstract mixin that provides audit fields and optimistic locking.
    
    Includes:
    - created_at, created_by
    - updated_at, updated_by  
    - version (for optimistic locking)
    - history (simple history tracking)
    """
    
    # Audit fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when record was created"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='%(app_label)s_%(class)s_created',
        help_text="User who created this record"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when record was last updated"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='%(app_label)s_%(class)s_updated',
        help_text="User who last updated this record"
    )
    
    # Optimistic locking
    version = models.PositiveIntegerField(
        default=1,
        help_text="Version number for optimistic locking"
    )
    
    # History tracking
    history = HistoricalRecords(inherit=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Save with optimistic locking check"""
        if self.pk:
            self._check_optimistic_locking()
            self.version += 1
        
        super().save(*args, **kwargs)
    
    def _check_optimistic_locking(self):
        """Check if record has been modified by another user"""
        try:
            current = self.__class__.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValidationError(
                    "Record has been modified by another user. "
                    "Please refresh and try again."
                )
        except self.__class__.DoesNotExist:
            # Record was deleted, allow save as new
            pass
    
    def refresh_version(self):
        """Refresh version from database"""
        if self.pk:
            current = self.__class__.objects.get(pk=self.pk)
            self.version = current.version
            return self.version
        return None
