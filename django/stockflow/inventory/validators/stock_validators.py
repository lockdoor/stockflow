"""
Stock Validators

Validation classes for Stock model to ensure data integrity
and business rule compliance.

Author: StockFlow Team  
Created: 2025
"""

from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import re


class StockQuantityValidator:
    """Validates stock quantity rules"""
    
    def __init__(self, stock):
        self.stock = stock
    
    def validate(self):
        """Validate quantity rules"""
        errors = {}
        
        # Check if available_quantity is not None
        if self.stock.available_quantity is None:
            errors['available_quantity'] = 'Available quantity is required'
            return errors
        
        # Check if available_quantity is not negative
        if self.stock.available_quantity < 0:
            errors['available_quantity'] = 'Available quantity cannot be negative'
        
        # Check reasonable upper limit (optional business rule)
        max_quantity = Decimal('999999.999')
        if self.stock.available_quantity > max_quantity:
            errors['available_quantity'] = f'Available quantity cannot exceed {max_quantity}'
        
        return errors if errors else None


class StockLotNumberValidator:
    """Validates lot number format and rules"""
    
    def __init__(self, stock):
        self.stock = stock
    
    def validate(self):
        """Validate lot number"""
        errors = {}
        
        if not self.stock.lot_number:
            errors['lot_number'] = 'Lot number is required'
            return errors
        
        # Check length
        if len(self.stock.lot_number) > 50:
            errors['lot_number'] = 'Lot number cannot exceed 50 characters'
        
        # Check for valid characters (alphanumeric, dash, underscore)
        if not re.match(r'^[A-Za-z0-9\-_]+$', self.stock.lot_number):
            errors['lot_number'] = 'Lot number can only contain letters, numbers, hyphens, and underscores'
        
        return errors if errors else None


class StockExpiryDateValidator:
    """Validates expiry date rules"""
    
    def __init__(self, stock):
        self.stock = stock
    
    def validate(self):
        """Validate expiry date"""
        errors = {}
        
        # Allow null expiry date (for items that don't expire)
        if not self.stock.expiry_date:
            return None
        
        # Check if expiry date is not too far in the past (more than 10 years)
        min_date = timezone.now().date().replace(year=timezone.now().year - 10)
        if self.stock.expiry_date < min_date:
            errors['expiry_date'] = 'Expiry date cannot be more than 10 years in the past'
        
        # Check if expiry date is not too far in the future (more than 20 years)
        max_date = timezone.now().date().replace(year=timezone.now().year + 20)
        if self.stock.expiry_date > max_date:
            errors['expiry_date'] = 'Expiry date cannot be more than 20 years in the future'
        
        return errors if errors else None


class StockBusinessRulesValidator:
    """Validates business rules for stock"""
    
    def __init__(self, stock):
        self.stock = stock
    
    def validate(self):
        """Validate business rules"""
        errors = []
        
        # Check if item_sku is provided
        if not self.stock.item_sku_id:
            errors.append('Item SKU is required')
        
        # Check if warehouse is provided
        if not self.stock.warehouse_id:
            errors.append('Warehouse is required')
        
        # Check if item_sku is active (if we have the instance)
        if hasattr(self.stock, 'item_sku') and self.stock.item_sku:
            if hasattr(self.stock.item_sku, 'status') and self.stock.item_sku.status == 'INACTIVE':
                errors.append('Cannot create stock for inactive item SKU')
        
        # Check if warehouse is active (if we have the instance)
        if hasattr(self.stock, 'warehouse') and self.stock.warehouse:
            if hasattr(self.stock.warehouse, 'is_active') and not self.stock.warehouse.is_active:
                errors.append('Cannot create stock for inactive warehouse')
        
        # Check for duplicate stock records (same item_sku, warehouse, lot_number, expiry_date)
        if self.stock.item_sku_id and self.stock.warehouse_id and self.stock.lot_number and self.stock.expiry_date:
            from inventory.models.stock import Stock
            
            existing_query = Stock.objects.filter(
                item_sku_id=self.stock.item_sku_id,
                warehouse_id=self.stock.warehouse_id,
                lot_number=self.stock.lot_number,
                expiry_date=self.stock.expiry_date
            )
            
            # Exclude current instance if we're updating
            if self.stock.pk:
                existing_query = existing_query.exclude(pk=self.stock.pk)
            
            if existing_query.exists():
                errors.append('Stock record with same item SKU, warehouse, lot number, and expiry date already exists')
        
        return errors if errors else None
