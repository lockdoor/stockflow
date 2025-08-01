"""
Stock Model

Represents stock balances for FEFO/FIFO inventory management.
Tracks available quantities per item SKU, warehouse, lot number, and expiry date.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal

from .warehouse import Warehouse
from catalog.models.item import ItemSKU
from common.mixins import AuditableMixin, ValidatableMixin

from inventory.validators import (
    StockQuantityValidator,
    StockLotNumberValidator,
    StockExpiryDateValidator,
    StockBusinessRulesValidator
)


class Stock(AuditableMixin, ValidatableMixin, models.Model):
    """
    Stock Model
    
    Represents stock balances for inventory management with FEFO/FIFO support.
    Each record represents a unique combination of item_sku, warehouse, lot_number, and expiry_date.
    
    Business Rules:
    - Available quantity must be >= 0
    - Lot number is required for tracking
    - Expiry date is required for FEFO
    - Unique constraint on (item_sku, warehouse, lot_number, expiry_date)
    """
    
    # Core fields
    item_sku = models.ForeignKey(
        ItemSKU,
        on_delete=models.PROTECT,
        related_name='stocks',
        help_text="Item SKU for this stock record"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='stocks',
        help_text="Warehouse where stock is located"
    )
    lot_number = models.CharField(
        max_length=50,
        help_text="Lot number for tracking and traceability"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expiry date for FEFO (First Expired, First Out) logic"
    )
    available_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text="Available quantity in stock"
    )
    
    # Audit fields (inherited from AuditableMixin)
    # created_at, updated_at
    
    class Meta:
        db_table = 'inventory_stock'
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
        ordering = ['warehouse', 'item_sku', 'expiry_date', 'lot_number']
        
        constraints = [
            # Ensure unique combination of item_sku, warehouse, lot_number, and expiry_date
            models.UniqueConstraint(
                fields=['item_sku', 'warehouse', 'lot_number', 'expiry_date'],
                name='unique_stock_record'
            ),
            # Ensure available_quantity is not negative
            models.CheckConstraint(
                check=models.Q(available_quantity__gte=0),
                name='positive_available_quantity'
            )
        ]
        
        indexes = [
            # For FEFO queries (earliest expiry first)
            models.Index(fields=['item_sku', 'warehouse', 'expiry_date']),
            # For FIFO queries (earliest lot first)
            models.Index(fields=['item_sku', 'warehouse', 'lot_number']),
            # For stock lookup
            models.Index(fields=['warehouse', 'item_sku']),
            # For expiry monitoring
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.item_sku.sku_code} @ {self.warehouse.code} - Lot: {self.lot_number} - Qty: {self.available_quantity}"
    
    def get_validators(self):
        """Return list of validator instances for this model"""
        return [
            StockQuantityValidator(self),
            StockLotNumberValidator(self),
            StockExpiryDateValidator(self),
            StockBusinessRulesValidator(self)
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
        """Save with validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # Business logic methods
    
    def is_expired(self):
        """Check if this stock record is expired"""
        if self.expiry_date is None:
            return False  # Items without expiry date never expire
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
    
    def days_to_expiry(self):
        """Get number of days until expiry (negative if expired)"""
        if self.expiry_date is None:
            return None  # Items without expiry date don't have days to expiry
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days
    
    def is_available(self):
        """Check if stock is available (quantity > 0)"""
        return self.available_quantity > 0
    
    def can_deduct(self, quantity):
        """Check if we can deduct the specified quantity"""
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        if quantity > self.available_quantity:
            return False, f"Insufficient stock. Available: {self.available_quantity}, Requested: {quantity}"
        
        return True, ""
    
    def deduct_quantity(self, quantity, user=None, save=True):
        """
        Deduct quantity from available stock.
        
        Args:
            quantity (Decimal): Amount to deduct
            user: User instance for audit trail
            save (bool): Whether to save the model after deduction
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValidationError: If deduction would result in negative stock
        """
        can_deduct, reason = self.can_deduct(quantity)
        if not can_deduct:
            raise ValidationError(reason)
        
        self.available_quantity -= quantity
        
        if user:
            self.updated_by = user
        
        if save:
            self.save()
        
        return True
    
    def add_quantity(self, quantity, user=None, save=True):
        """
        Add quantity to available stock.
        
        Args:
            quantity (Decimal): Amount to add
            user: User instance for audit trail
            save (bool): Whether to save the model after addition
            
        Returns:
            bool: True if successful
            
        Raises:
            ValidationError: If quantity is not positive
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        self.available_quantity += quantity
        
        if user:
            self.updated_by = user
        
        if save:
            self.save()
        
        return True
    
    @classmethod
    def get_stock_for_item(cls, item_sku, warehouse):
        """
        Get all stock records for a specific item in a warehouse.
        
        Args:
            item_sku: ItemSKU instance
            warehouse: Warehouse instance
            
        Returns:
            QuerySet: Stock records ordered by expiry date (FEFO)
        """
        return cls.objects.filter(
            item_sku=item_sku,
            warehouse=warehouse,
            available_quantity__gt=0
        ).order_by(
            models.F('expiry_date').asc(nulls_last=True), 
            'lot_number'
        )
    
    @classmethod
    def get_total_stock(cls, item_sku, warehouse):
        """
        Get total available stock for an item in a warehouse.
        
        Args:
            item_sku: ItemSKU instance
            warehouse: Warehouse instance
            
        Returns:
            Decimal: Total available quantity
        """
        result = cls.objects.filter(
            item_sku=item_sku,
            warehouse=warehouse
        ).aggregate(
            total=models.Sum('available_quantity')
        )
        return result['total'] or Decimal('0.000')
    
    @classmethod
    def get_all_stock(cls):
        """
        Get all stock records across all warehouses.
        Aggregate quantities by item SKU and warehouse, showing only available stock.
        This is useful for reporting and inventory checks.
        
        Returns:
            QuerySet: Dict records with item_sku_id, warehouse_id, sku_code, warehouse_code, and total_quantity
        """
        return cls.objects.filter(
            available_quantity__gt=0
        ).values(
            'item_sku__id',
            'item_sku__sku_code',
            'item_sku__name',
            'warehouse__id',
            'warehouse__code'
        ).annotate(
            total_quantity=models.Sum('available_quantity')
        ).order_by('warehouse__code', 'item_sku__sku_code')
    
    @classmethod
    def find_or_create_stock(cls, item_sku, warehouse, lot_number, expiry_date, user):
        """
        Find existing stock record or create new one.
        
        Args:
            item_sku: ItemSKU instance
            warehouse: Warehouse instance
            lot_number: String lot number
            expiry_date: Date expiry date
            user: User instance for audit fields
            
        Returns:
            tuple: (Stock instance, created boolean)
        """
        try:
            stock = cls.objects.get(
                item_sku=item_sku,
                warehouse=warehouse,
                lot_number=lot_number,
                expiry_date=expiry_date
            )
            return stock, False
        except cls.DoesNotExist:
            stock = cls.objects.create(
                item_sku=item_sku,
                warehouse=warehouse,
                lot_number=lot_number,
                expiry_date=expiry_date,
                available_quantity=Decimal('0.000'),
                created_by=user,
                updated_by=user
            )
            return stock, True
    
    @classmethod
    def allocate_stock_fifo(cls, item_sku, warehouse, quantity_needed):
        """
        Allocate stock using FIFO (First In, First Out) logic.
        
        Args:
            item_sku: ItemSKU instance
            warehouse: Warehouse instance
            quantity_needed: Decimal quantity to allocate
            
        Returns:
            list: List of (stock_record, allocated_quantity) tuples
            
        Raises:
            ValidationError: If insufficient stock available
        """
        available_stocks = cls.get_stock_for_item(item_sku, warehouse)
        total_available = sum(stock.available_quantity for stock in available_stocks)
        
        if total_available < quantity_needed:
            raise ValidationError(
                f"Insufficient stock. Available: {total_available}, Needed: {quantity_needed}"
            )
        
        allocations = []
        remaining_quantity = quantity_needed
        
        for stock in available_stocks:
            if remaining_quantity <= 0:
                break
            
            allocated_qty = min(stock.available_quantity, remaining_quantity)
            allocations.append((stock, allocated_qty))
            remaining_quantity -= allocated_qty
        
        return allocations
    
    @classmethod
    def allocate_stock_fefo(cls, item_sku, warehouse, quantity_needed, user):
        """
        Allocate stock using FEFO (First Expired, First Out) logic with pessimistic locking.
        
        Args:
            item_sku: ItemSKU instance
            warehouse: Warehouse instance
            quantity_needed: Decimal quantity to allocate
            user: User instance for audit trail
            
        Returns:
            list: List of (stock_record, allocated_quantity) tuples
            
        Raises:
            ValidationError: If insufficient stock available
        """
        from django.db import transaction
        
        # Use select_for_update to prevent concurrent modifications
        # Order by expiry_date (nulls last), then lot_number for FEFO logic
        available_stocks = cls.objects.filter(
            item_sku=item_sku,
            warehouse=warehouse,
            available_quantity__gt=0
        ).select_for_update().order_by(
            models.F('expiry_date').asc(nulls_last=True), 
            'lot_number'
        )
        
        total_available = sum(stock.available_quantity for stock in available_stocks)
        
        if total_available < quantity_needed:
            raise ValidationError(
                f"Insufficient stock. Available: {total_available}, Needed: {quantity_needed}"
            )
        
        allocations = []
        remaining_quantity = quantity_needed
        
        for stock in available_stocks:
            if remaining_quantity <= 0:
                break
            
            allocated_qty = min(stock.available_quantity, remaining_quantity)
            allocations.append((stock, allocated_qty))
            remaining_quantity -= allocated_qty
        
        return allocations
