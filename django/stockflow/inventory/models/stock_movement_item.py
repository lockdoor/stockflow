"""
Stock Movement Item Model

This module defines the StockMovementItem model which represents individual items
within a stock movement transaction. Each item has movement type, quantity,
lot information, and audit trails.

Author: StockFlow Team
Created: 2025
"""

from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError

from inventory.models.stock_movement import StockMovement
from catalog.models.item import ItemSKU
from common.mixins import AuditableMixin, ValidatableMixin
from common.mixins.immutable import ImmutableMixin
from inventory.validators import (
    StockMovementItemQuantityValidator,
    StockMovementItemLotValidator,
    StockMovementItemBusinessRulesValidator,
    StockMovementItemExpiryValidator,
    StockMovementItemDuplicateValidator
)

class StockMovementItem(
    AuditableMixin,
    ValidatableMixin,
    ImmutableMixin,
    models.Model
):
    """
    Represents individual items within a stock movement transaction.
    
    Each StockMovementItem belongs to a StockMovement and contains details
    about the specific item being moved, including quantity, lot information,
    and movement direction (IN/OUT).
    
    Business Rules:
    - Cannot modify items in CONFIRMED stock movements
    - Uses optimistic locking via AuditableMixin
    - Unique constraint on (stock_movement, item_sku, lot_number, movement_type)
    """
    
    class MovementType(models.TextChoices):
        """Movement direction choices"""
        IN = 'IN', 'Stock In'
        OUT = 'OUT', 'Stock Out'

    # Core relationships
    stock_movement = models.ForeignKey(
        StockMovement, 
        on_delete=models.CASCADE, 
        related_name='movement_items',
        help_text="Parent stock movement transaction"
    )
    item_sku = models.ForeignKey(
        ItemSKU, 
        on_delete=models.PROTECT,
        help_text="Item being moved"
    )
    
    # Movement details
    movement_type = models.CharField(
        max_length=3, 
        choices=MovementType.choices,
        help_text="Direction of stock movement (IN/OUT)"
    )
    quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Quantity being moved"
    )
    
    # Lot tracking
    lot_number = models.CharField(
        max_length=64, 
        blank=False, 
        null=False,
        help_text="Lot or batch number for traceability"
    )
    expiry_date = models.DateField(
        blank=True, 
        null=True,
        help_text="Expiration date for the lot"
    )
    
    # Additional information
    note = models.TextField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Additional notes for this movement item"
    )
    
    # Audit fields inherited from AuditableMixin:
    # created_by, updated_by, created_at, updated_at, version
    
    # History tracking (commented out due to multiple registration issue)
    # history = HistoricalRecords()

    class Meta:
        db_table = 'inventory_stock_movement_item'
        unique_together = ('stock_movement', 'item_sku', 'lot_number', 'movement_type')
        verbose_name = 'Stock Movement Item'
        verbose_name_plural = 'Stock Movement Items'
        ordering = ['-created_at', 'item_sku__sku_code']
        indexes = [
            models.Index(fields=['stock_movement', 'item_sku']),
            models.Index(fields=['movement_type', 'created_at']),
            models.Index(fields=['lot_number']),
        ]

    def __str__(self):
        """String representation of the movement item"""
        return f"{self.item_sku.sku_code} ({self.get_movement_type_display()}) x {self.quantity}"

    def get_validators(self):
        """Return list of validator instances for this model"""
        return [
            StockMovementItemQuantityValidator(self),
            StockMovementItemLotValidator(self),
            StockMovementItemExpiryValidator(self),
            StockMovementItemDuplicateValidator(self),
            StockMovementItemBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """
        Save with validation and business logic.
        
        The order of mixins matters:
        1. ValidatableMixin calls clean() first
        2. ImmutableMixin handles immutability check
        3. AuditableMixin sets audit fields and optimistic locking
        4. Model.save() persists to database
        """
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Delete with immutability check.
        ImmutableMixin will prevent deletion if parent movement is CONFIRMED.
        """
        super().delete(*args, **kwargs)

    # ImmutableMixin implementation
    def is_immutable(self):
        """Return True if parent stock movement is confirmed"""
        return (hasattr(self, 'stock_movement') and 
                self.stock_movement and 
                self.stock_movement.status == StockMovement.Status.CONFIRMED)

    def get_immutable_reason(self):
        """Return reason why this record is immutable"""
        return "Cannot modify items in confirmed stock movements"

    # Business logic methods
    def can_modify(self):
        """Check if this item can be modified"""
        return not self.is_immutable()

    @property
    def is_inbound(self):
        """Check if this is an inbound movement"""
        return self.movement_type == self.MovementType.IN

    @property
    def is_outbound(self):
        """Check if this is an outbound movement"""
        return self.movement_type == self.MovementType.OUT

    def get_display_name(self):
        """Get formatted display name for this movement item"""
        direction = "←" if self.is_inbound else "→"
        return f"{direction} {self.item_sku.name} (x{self.quantity})"