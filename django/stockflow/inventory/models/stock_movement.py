"""
Stock Movement Model

Represents stock movements in warehouses with immutable confirmed status,
optimistic locking, and comprehensive business rule validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.core.exceptions import ValidationError

from .warehouse import Warehouse
from common.mixins import AuditableMixin, ValidatableMixin
from common.mixins.immutable import ImmutableMixin

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
    ImmutableMixin,
    models.Model
):
    """
    Stock Movement Model
    
    Represents movements of stock in/out of warehouses. Can be in DRAFT or COMPLETED status.
    Once COMPLETED, the record becomes immutable for audit trail integrity.
    
    Business Rules:
    - Only one DRAFT stock movement per warehouse at a time
    - COMPLETED status makes record immutable
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
        PROCESSING = 'PROCESSING', 'Processing Stock Changes'
        COMPLETED = 'COMPLETED', 'Stock Changes Completed'
        FAILED = 'FAILED', 'Stock Processing Failed'

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
        ImmutableMixin will prevent deletion if status is COMPLETED.
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
        
        # Check if movement has items - movement_items is the reverse relation name
        if hasattr(self, 'movement_items') and not self.movement_items.exists():
            return False, "Cannot confirm movement without items"
        
        return True, ""
    
    def confirm(self, user):
        """
        Confirm this stock movement with proper transaction handling.
        This makes the record immutable and processes stock changes atomically.
        """
        from django.db import transaction
        
        can_confirm, reason = self.can_be_confirmed()
        if not can_confirm:
            raise ValidationError(reason)
        
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Set status to PROCESSING to indicate we're working on it
            self.status = self.Status.PROCESSING
            self.updated_by = user
            
            # Override immutability check for this specific save
            self._confirming = True
            try:
                self.save()
                
                # Process stock changes after movement is confirmed
                self._process_stock_changes()
                
                # Mark as completed
                self.status = self.Status.COMPLETED
                self.save()
                
            except Exception as e:
                # Mark as failed for later recovery
                self.status = self.Status.FAILED
                self.save()
                raise ValidationError(f"Failed to confirm movement: {str(e)}")
            finally:
                if hasattr(self, '_confirming'):
                    del self._confirming
        
        return True
    
    def _process_stock_changes(self):
        """
        Process stock changes for all movement items.
        This method is called within the confirm transaction.
        """
        if not hasattr(self, 'movement_items'):
            return  # No items to process
        
        from .stock import Stock
        from django.db import transaction
        
        # Process each movement item
        for item in self.movement_items.all():
            if item.movement_type == 'IN':
                self._process_stock_in(item, self.updated_by)
            elif item.movement_type == 'OUT':
                self._process_stock_out(item, self.updated_by)
    
    def _process_stock_in(self, movement_item, user):
        """Process stock IN (receiving inventory)"""
        from .stock import Stock
        
        # Find or create stock record
        stock, created = Stock.find_or_create_stock(
            item_sku=movement_item.item_sku,
            warehouse=self.warehouse,
            lot_number=movement_item.lot_number,
            expiry_date=movement_item.expiry_date,
            user=user  # Pass user for created_by/updated_by
        )
        
        # Add quantity to stock
        stock.add_quantity(movement_item.quantity, user=user, save=True)
    
    def _process_stock_out(self, movement_item, user):
        """Process stock OUT (consuming inventory) with FEFO"""
        from .stock import Stock
        
        # Allocate stock using FEFO logic
        allocations = Stock.allocate_stock_fefo(
            item_sku=movement_item.item_sku,
            warehouse=self.warehouse,
            quantity_needed=movement_item.quantity,
            user=user  # Pass user for audit trail
        )
        
        # Deduct quantities from allocated stock records
        for stock_record, allocated_qty in allocations:
            stock_record.deduct_quantity(allocated_qty, user=user, save=True)
    
    def can_be_recovered(self):
        """Check if this movement can be recovered from failed state"""
        return self.status in [self.Status.PROCESSING, self.Status.FAILED]
    
    def recover(self, user):
        """
        Recover a failed stock movement.
        Attempts to complete the stock processing that was interrupted.
        """
        if not self.can_be_recovered():
            raise ValidationError("Movement cannot be recovered from current state")
        
        from django.db import transaction
        
        with transaction.atomic():
            # Reset to processing state
            self.status = self.Status.PROCESSING
            self.updated_by = user
            
            self._confirming = True
            try:
                self.save()
                
                # Attempt to process stock changes again
                self._process_stock_changes()
                
                # Mark as completed
                self.status = self.Status.COMPLETED
                self.save()
                
            except Exception as e:
                # Mark as failed again
                self.status = self.Status.FAILED
                self.save()
                raise ValidationError(f"Recovery failed: {str(e)}")
            finally:
                if hasattr(self, '_confirming'):
                    del self._confirming
        
        return True
    
    @classmethod
    def get_failed_movements(cls):
        """Get all movements that need recovery"""
        return cls.objects.filter(
            status__in=[cls.Status.PROCESSING, cls.Status.FAILED]
        ).order_by('created_at')
    
    @classmethod 
    def bulk_recover_failed_movements(cls, user):
        """
        Bulk recovery for failed movements.
        Should be run as a management command or scheduled task.
        """
        failed_movements = cls.get_failed_movements()
        recovered = 0
        still_failed = 0
        
        for movement in failed_movements:
            try:
                movement.recover(user)
                recovered += 1
            except ValidationError:
                still_failed += 1
                continue
        
        return {
            'recovered': recovered,
            'still_failed': still_failed,
            'total_processed': len(failed_movements)
        }
    
    def get_total_items_count(self):
        """Get total number of items in this movement"""
        if hasattr(self, 'movement_items'):
            return self.movement_items.count()
        return 0
    
    def get_reference_display(self):
        """Get formatted reference display"""
        if self.reference_type == self.ReferenceType.NONE:
            return "No Reference"
        
        if self.reference_id:
            return f"{self.get_reference_type_display()} #{self.reference_id}"
        
        return self.get_reference_type_display()
    
    # ImmutableMixin implementation
    def is_immutable(self):
        """Return True if this stock movement is immutable (status is COMPLETED)"""
        # Allow confirmation process to proceed
        if hasattr(self, '_confirming'):
            return False
        return self.status == self.Status.COMPLETED
    
    def get_immutable_reason(self):
        """Return reason why this record is immutable"""
        return "Completed stock movements cannot be modified for audit trail integrity"
