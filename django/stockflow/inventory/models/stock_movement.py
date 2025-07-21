"""
Stock Movement Model

Represents stock movements in warehouses with immutable confirmed status,
optimistic locking, and comprehensive business rule validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from .warehouse import Warehouse
from common.mixins import AuditableMixin, ValidatableMixin
from inventory.mixins import StatusImmutableMixin, VersionedImmutableMixin
from inventory.validators import (
    StockMovementStatusValidator,
    StockMovementReferenceValidator,
    StockMovementWarehouseValidator,
    StockMovementBusinessRulesValidator,
    StockMovementVersionValidator
)

class StockMovement(
    AuditableMixin,
    ValidatableMixin, 
    StatusImmutableMixin,
    VersionedImmutableMixin,
    models.Model
):
    """
    Stock Movement Model
    
    Represents movements of stock in/out of warehouses. Can be in DRAFT or CONFIRMED status.
    Once CONFIRMED, the record becomes immutable for audit trail integrity.
    
    Business Rules:
    - Only one DRAFT stock movement per warehouse at a time
    - CONFIRMED status makes record immutable
    - Optimistic locking via version field
    - Reference type and ID must be consistent
    """
    
    class ReferenceType(models.TextChoices):
        NONE = 'NONE', 'None'
        ADJUST = 'ADJUST', 'Adjust'
        PACKING_LIST = 'PACKING_LIST', 'Packing List'
        PRODUCTION = 'PRODUCTION', 'Production'
        INVOICE = 'INVOICE', 'Invoice'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
    
    # Immutable statuses for StatusImmutableMixin
    IMMUTABLE_STATUSES = [Status.CONFIRMED]

    # Core fields
    reference_type = models.CharField(
        max_length=20,
        choices=ReferenceType.choices,
        default=ReferenceType.NONE,
        help_text="Type of document this movement references"
    )
    reference_id = models.IntegerField(
        null=True, 
        blank=True,
        help_text="ID of the referenced document"
    )
    note = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes about this stock movement"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        help_text="Warehouse where this stock movement occurs"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status of the stock movement"
    )
    
    # Audit fields (inherited from AuditableMixin)
    # created_at, created_by, updated_at, updated_by, version
    
    # History tracking (commented out due to multiple registration issue)
    # history = HistoricalRecords()

    class Meta:
        db_table = 'inventory_stock_movement'
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-created_at', '-id']
        
        constraints = [
            # Ensure only one draft stock movement per warehouse
            models.UniqueConstraint(
                fields=['warehouse'],
                condition=models.Q(status='DRAFT'),
                name='unique_draft_per_warehouse'
            )
        ]
        
        indexes = [
            models.Index(fields=['warehouse', 'status']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Stock Movement #{self.id} ({self.status}) - {self.warehouse.name}"
    
    def get_validators(self):
        """Return list of validator instances for this model"""
        return [
            StockMovementStatusValidator(self),
            StockMovementReferenceValidator(self),
            StockMovementWarehouseValidator(self),
            StockMovementBusinessRulesValidator(self),
            StockMovementVersionValidator(self)
        ]
    
    def clean(self):
        """Run all validation before saving"""
        super().clean()
        
        # Run custom validators
        errors = {}
        for validator in self.get_validators():
            error_message = validator.validate()
            if error_message:
                # Simple string errors go to non_field_errors
                if isinstance(error_message, str):
                    if '__all__' not in errors:
                        errors['__all__'] = []
                    errors['__all__'].append(error_message)
                # Dict errors get merged
                elif isinstance(error_message, dict):
                    errors.update(error_message)
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Save with validation and business logic.
        
        The order of mixins matters:
        1. ValidatableMixin calls clean() first
        2. VersionedImmutableMixin handles version and immutability
        3. AuditableMixin sets audit fields
        4. Model.save() persists to database
        """
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Delete with immutability check.
        StatusImmutableMixin will prevent deletion if status is CONFIRMED.
        """
        super().delete(*args, **kwargs)
    
    # Business logic methods
    
    def can_be_modified(self):
        """Check if this stock movement can be modified"""
        return not self.is_immutable()
    
    def can_be_confirmed(self):
        """Check if this stock movement can be confirmed"""
        if self.status != self.Status.DRAFT:
            return False, "Only draft movements can be confirmed"
        
        # Check if movement has items
        if hasattr(self, 'stock_movement_items') and not self.stock_movement_items.exists():
            return False, "Cannot confirm movement without items"
        
        return True, ""
    
    def confirm(self, user):
        """
        Confirm this stock movement.
        This makes the record immutable.
        """
        can_confirm, reason = self.can_be_confirmed()
        if not can_confirm:
            raise ValidationError(reason)
        
        self.status = self.Status.CONFIRMED
        self.updated_by = user
        self.save()
        
        # TODO: Trigger stock balance updates when Stock model is implemented
        
        return True
    
    def get_total_items_count(self):
        """Get total number of items in this movement"""
        if hasattr(self, 'stock_movement_items'):
            return self.stock_movement_items.count()
        return 0
    
    def get_reference_display(self):
        """Get formatted reference display"""
        if self.reference_type == self.ReferenceType.NONE:
            return "No Reference"
        
        if self.reference_id:
            return f"{self.get_reference_type_display()} #{self.reference_id}"
        
        return self.get_reference_type_display()
