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
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from inventory.models.stock_movement import StockMovement
from catalog.models.item import ItemSKU

class StockMovementItem(models.Model):
    """
    Represents individual items within a stock movement transaction.
    
    Each StockMovementItem belongs to a StockMovement and contains details
    about the specific item being moved, including quantity, lot information,
    and movement direction (IN/OUT).
    
    Business Rules:
    - Cannot modify items in CONFIRMED stock movements
    - Uses optimistic locking to prevent concurrent updates
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
        blank=True, 
        null=True,
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
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='stock_movement_items_created',
        help_text="User who created this movement item"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='stock_movement_items_updated',
        help_text="User who last updated this movement item"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optimistic locking
    version = models.PositiveIntegerField(
        default=0,
        help_text="Version number for optimistic locking"
    )
    
    # History tracking
    history = HistoricalRecords()

    class Meta:
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

    def _validate_item_sku(self) -> str | None:
        """Validate item SKU business rules"""
        if not self.item_sku:
            return "Item SKU is required"
            
        if self.item_sku.status != ItemSKU.Status.ACTIVE:
            return f"Cannot move inactive item SKU ({self.item_sku.get_status_display()})"
        return None
        
    def _get_stock_movement(self):
        """Safely get stock_movement, returns None if not set"""
        try:
            return self.stock_movement
        except StockMovement.DoesNotExist:
            return None

    def _validate_quantity(self) -> str | None:
        """Validate quantity business rules"""
        if self.quantity is None:
            return "Quantity is required"
            
        if self.quantity <= 0:
            return "Quantity must be greater than zero"
            
        # Check maximum decimal places (2)
        if self.quantity.as_tuple().exponent < -2:
            return "Quantity cannot have more than 2 decimal places"
            
        # Check reasonable maximum quantity (prevent data entry errors)
        max_quantity = 999999.99
        if self.quantity > max_quantity:
            return f"Quantity cannot exceed {max_quantity:,.2f}"
            
        return None
    
    def _validate_expiry_date(self) -> str | None:
        """Validate expiry date business rules"""
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return "Expiry date cannot be in the past"
            
        # Check if expiry date is too far in the future (e.g., 50 years)
        if self.expiry_date:
            max_future_date = timezone.now().date().replace(year=timezone.now().year + 50)
            if self.expiry_date > max_future_date:
                return "Expiry date cannot be more than 50 years in the future"
                
        return None

    def _validate_movement_type_consistency(self) -> str | None:
        """Validate movement type consistency with parent stock movement"""
        stock_movement_id = getattr(self, 'stock_movement_id', None)
        if not stock_movement_id:
            return "Stock movement is required"
            
        # Note: StockMovement doesn't have movement_type field in current implementation
        # This validation can be extended if movement types are added to StockMovement
        # For now, we just ensure stock movement exists
        return None

    def _validate_lot_number(self) -> str | None:
        """Validate lot number business rules"""
        if self.lot_number:
            # Check lot number format (alphanumeric with some special chars)
            import re
            if not re.match(r'^[A-Za-z0-9\-_/]+$', self.lot_number):
                return "Lot number can only contain letters, numbers, hyphens, underscores, and forward slashes"
                
            # Check lot number length
            if len(self.lot_number) > 64:
                return "Lot number cannot exceed 64 characters"
                
        # For certain item types, lot number might be required
        if self.item_sku and self.item_sku.type in [ItemSKU.Type.RAW, ItemSKU.Type.PACKAGE]:
            if not self.lot_number:
                return f"Lot number is required for {self.item_sku.get_type_display()} items"
                
        return None

    def _validate_outbound_quantity(self) -> str | None:
        """Validate outbound quantity against available stock"""
        if self.movement_type != self.MovementType.OUT:
            return None
            
        # Skip validation for new stock movements (not yet confirmed)
        stock_movement = self._get_stock_movement()
        if not stock_movement or stock_movement.status == StockMovement.Status.DRAFT:
            return None
            
        # TODO: Implement stock level checking
        # This would require a stock level tracking system
        # available_stock = get_available_stock(self.item_sku, stock_movement.warehouse, self.lot_number)
        # if self.quantity > available_stock:
        #     return f"Insufficient stock. Available: {available_stock}, Requested: {self.quantity}"
            
        return None

    def _validate_warehouse_item_compatibility(self) -> str | None:
        """Validate that item can be stored/moved in the warehouse"""
        stock_movement = self._get_stock_movement()
        if not stock_movement or not stock_movement.warehouse:
            return None
            
        # Check if warehouse is active
        if not stock_movement.warehouse.is_active:
            return "Cannot move items to/from inactive warehouse"
            
        # TODO: Implement warehouse-item compatibility rules
        # e.g., temperature controlled items, hazardous materials, etc.
        
        return None

    def _validate_duplicate_item_in_movement(self) -> str | None:
        """Validate no duplicate items in same movement with same lot"""
        stock_movement = self._get_stock_movement()
        if not stock_movement:
            return None
            
        # Check for existing items in the same movement
        existing_items = StockMovementItem.objects.filter(
            stock_movement=stock_movement,
            item_sku=self.item_sku,
            movement_type=self.movement_type,
            lot_number=self.lot_number or ''
        )
        
        # Exclude current item if updating
        if self.pk:
            existing_items = existing_items.exclude(pk=self.pk)
            
        if existing_items.exists():
            lot_info = f" with lot {self.lot_number}" if self.lot_number else " without lot number"
            return f"Item {self.item_sku.sku_code} ({self.get_movement_type_display()}){lot_info} already exists in this movement"
            
        return None

    def _validate_note_length(self) -> str | None:
        """Validate note field"""
        if self.note and len(self.note) > 500:
            return "Note cannot exceed 500 characters"
        return None

    def _validate_business_rules(self) -> str | None:
        """Validate complex business rules"""
        errors = []
        
        # Check if item requires special handling
        if self.item_sku and hasattr(self.item_sku, 'requires_temperature_control'):
            if self.item_sku.requires_temperature_control and not self.expiry_date:
                errors.append("Temperature controlled items must have expiry date")
        
        # Check movement date consistency
        stock_movement = self._get_stock_movement()
        if stock_movement and stock_movement.created_at:
            if self.created_at and stock_movement.created_at.date() > self.created_at.date():
                errors.append("Movement date cannot be in the future relative to creation date")
        
        return "; ".join(errors) if errors else None

    def clean(self):
        """
        Model-level validation - handles business logic validation
        Calls individual validation methods for each field
        Raises ValidationError for business logic violations which will be converted to ValueError in save()
        """
        errors = []
        
        # Call field-specific validation methods
        field_validations = [
            self._validate_item_sku(),
            self._validate_quantity(),
            self._validate_expiry_date(),
            self._validate_movement_type_consistency(),
            self._validate_lot_number(),
            self._validate_outbound_quantity(),
            self._validate_warehouse_item_compatibility(),
            self._validate_duplicate_item_in_movement(),
            self._validate_note_length(),
            self._validate_business_rules()
        ]

        # Add non-None validation errors
        errors.extend([error for error in field_validations if error])
        
        if errors:
            raise ValidationError("; ".join(errors))

    def save(self, *args, **kwargs):
        """Save with business logic validation"""
        # Full clean validation
        self.full_clean()
        
        # Check if this is an update to existing record
        if self.pk:
            try:
                current = StockMovementItem.objects.get(pk=self.pk)
                
                # Check if movement is confirmed
                if current.stock_movement.status == StockMovement.Status.CONFIRMED:
                    raise ValidationError("Cannot modify confirmed stock movement items")
                
                # Optimistic locking check
                if current.version != self.version:
                    raise ValidationError("Record has been modified by another user. Please refresh and try again")
                
                # Increment version
                self.version += 1
                
            except StockMovementItem.DoesNotExist:
                # Record was deleted, allow save as new
                pass
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete with business logic validation"""
        stock_movement = self._get_stock_movement()
        if stock_movement and stock_movement.status == StockMovement.Status.CONFIRMED:
            raise ValidationError("Cannot delete item from confirmed stock movement")
        
        super().delete(*args, **kwargs)

    @property
    def is_inbound(self):
        """Check if this is an inbound movement"""
        return self.movement_type == self.MovementType.IN

    @property
    def is_outbound(self):
        """Check if this is an outbound movement"""
        return self.movement_type == self.MovementType.OUT

    @property
    def can_modify(self):
        """Check if this item can be modified"""
        stock_movement = self._get_stock_movement()
        return not stock_movement or stock_movement.status != StockMovement.Status.CONFIRMED

    def get_display_name(self):
        """Get formatted display name for this movement item"""
        direction = "←" if self.is_inbound else "→"
        return f"{direction} {self.item_sku.name} (x{self.quantity})"