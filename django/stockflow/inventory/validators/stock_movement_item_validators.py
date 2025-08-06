"""
Stock Movement Item Validators

Domain-specific validators for StockMovementItem model business rules.

Author: StockFlow Team
Created: 2025
"""

import re
import uuid
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError


class StockMovementItemQuantityValidator:
    """Validator for quantity field business rules"""
    
    def __init__(self, stock_movement_item):
        self.item = stock_movement_item
    
    def validate(self):
        """Validate quantity business rules"""
        if self.item.quantity is None:
            return "Quantity is required"
            
        if self.item.quantity <= 0:
            return "Quantity must be greater than zero"
            
        # Check maximum decimal places (2)
        if self.item.quantity.as_tuple().exponent < -2:
            return "Quantity cannot have more than 2 decimal places"
            
        # Check reasonable maximum quantity (prevent data entry errors)
        max_quantity = Decimal('999999.99')
        if self.item.quantity > max_quantity:
            return f"Quantity cannot exceed {max_quantity:,.2f}"
            
        return None


class StockMovementItemLotValidator:
    """Validator for lot number business rules with auto-generation and uniqueness"""
    
    def __init__(self, stock_movement_item):
        self.item = stock_movement_item
    
    def generate_lot_number(self):
        """Generate a unique lot number if not provided"""
        if self.item.lot_number:
            return  # Already has a lot number
        
        # Import here to avoid circular import
        from inventory.models.stock_movement_item import StockMovementItem
        
        # Generate format: {YYYYMMDD}-{HHMMSS}-{SHORT_UUID}
        now = timezone.now()
        base_format = now.strftime("%Y%m%d-%H%M%S")
        
        # Generate unique lot number
        max_attempts = 10
        for attempt in range(max_attempts):
            # Use first 8 characters of UUID for uniqueness
            short_uuid = str(uuid.uuid4())[:8].upper()
            potential_lot = f"{base_format}-{short_uuid}"
            
            # Check if this lot number already exists in the same movement
            existing = StockMovementItem.objects.filter(
                stock_movement=self.item.stock_movement,
                item_sku=self.item.item_sku,
                movement_type=self.item.movement_type,
                lot_number=potential_lot
            )
            
            # Exclude current item if updating
            if self.item.pk:
                existing = existing.exclude(pk=self.item.pk)
            
            if not existing.exists():
                self.item.lot_number = potential_lot
                return
        
        # Fallback if all attempts failed (very unlikely)
        self.item.lot_number = f"{base_format}-{uuid.uuid4()}"
    
    def validate(self):
        """Validate lot number business rules and generate if needed"""
        # Auto-generate lot number if not provided
        if not self.item.lot_number:
            self.generate_lot_number()
        
        # Validate lot number format
        if self.item.lot_number:
            # Check lot number format (alphanumeric with some special chars)
            if not re.match(r'^[A-Za-z0-9\-_/]+$', self.item.lot_number):
                return "Lot number can only contain letters, numbers, hyphens, underscores, and forward slashes"
                
            # Check lot number length
            if len(self.item.lot_number) > 64:
                return "Lot number cannot exceed 64 characters"
        
        # Check uniqueness within the same movement, item, and movement type
        if (self.item.lot_number and 
            (hasattr(self.item, 'stock_movement') and self.item.stock_movement or 
             getattr(self.item, 'stock_movement_id', None)) and 
            (hasattr(self.item, 'item_sku') and getattr(self.item, 'item_sku', None))):
            from inventory.models.stock_movement_item import StockMovementItem
            
            # Get stock_movement either from relation or ID
            stock_movement = (self.item.stock_movement 
                            if hasattr(self.item, 'stock_movement') and self.item.stock_movement
                            else self.item.stock_movement_id)
            
            existing_items = StockMovementItem.objects.filter(
                stock_movement=stock_movement,
                item_sku=self.item.item_sku,
                movement_type=self.item.movement_type,
                lot_number=self.item.lot_number
            )
            
            # Exclude current item if updating
            if self.item.pk:
                existing_items = existing_items.exclude(pk=self.item.pk)
            
            if existing_items.exists():
                return f"Lot number '{self.item.lot_number}' already exists for this item in this movement"
        
        # For certain item types, lot number might be required (now always generated)
        if ((hasattr(self.item, 'item_sku') and getattr(self.item, 'item_sku', None)) and 
            hasattr(self.item.item_sku, 'type') and
            self.item.item_sku.type in ['RAW', 'PACKAGE']):
            if not self.item.lot_number:
                return f"Lot number is required for {self.item.item_sku.get_type_display()} items"
                
        return None


class StockMovementItemExpiryValidator:
    """Validator for expiry date business rules"""
    
    def __init__(self, stock_movement_item):
        self.item = stock_movement_item
    
    def validate(self):
        """Validate expiry date business rules"""
        if self.item.expiry_date and self.item.expiry_date < timezone.now().date():
            return "Expiry date cannot be in the past"
            
        # Check if expiry date is too far in the future (e.g., 50 years)
        if self.item.expiry_date:
            max_future_date = timezone.now().date().replace(year=timezone.now().year + 50)
            if self.item.expiry_date > max_future_date:
                return "Expiry date cannot be more than 50 years in the future"
                
        return None


class StockMovementItemDuplicateValidator:
    """Validator for duplicate items in same movement (fallback check)"""
    
    def __init__(self, stock_movement_item):
        self.item = stock_movement_item
    
    def validate(self):
        """Validate no duplicate items in same movement with same lot"""
        # Check if stock_movement is available (either as relation or ID)
        has_stock_movement = (
            (hasattr(self.item, 'stock_movement') and self.item.stock_movement) or
            getattr(self.item, 'stock_movement_id', None)
        )
        
        if not has_stock_movement:
            return "Stock movement is required"
        
        # This is now primarily a fallback check since lot numbers are auto-generated
        # and uniqueness is handled in StockMovementItemLotValidator
        
        # Import here to avoid circular import
        from inventory.models.stock_movement_item import StockMovementItem
        
        # Get stock_movement either from relation or ID
        stock_movement = (self.item.stock_movement 
                        if hasattr(self.item, 'stock_movement') and self.item.stock_movement
                        else self.item.stock_movement_id)
        
        # Only check if lot_number is explicitly empty/None (rare case)
        if self.item.lot_number is None or self.item.lot_number == '':
            existing_items = StockMovementItem.objects.filter(
                stock_movement=stock_movement,
                item_sku=self.item.item_sku,
                movement_type=self.item.movement_type,
                lot_number__isnull=True
            )
            
            # Exclude current item if updating
            if self.item.pk:
                existing_items = existing_items.exclude(pk=self.item.pk)
                
            if existing_items.exists():
                return f"Item {self.item.item_sku.sku_code} ({self.item.get_movement_type_display()}) without lot number already exists in this movement"
            
        return None


class StockMovementItemBusinessRulesValidator:
    """Validator for complex business rules"""
    
    def __init__(self, stock_movement_item):
        self.item = stock_movement_item
    
    def validate(self):
        """Validate complex business rules"""
        errors = []
        
        # Validate item SKU is active
        item_sku = getattr(self.item, 'item_sku', None)
        if item_sku and hasattr(item_sku, 'status'):
            if item_sku.status != 'ACTIVE':
                errors.append(f"Cannot move inactive item SKU ({item_sku.get_status_display()})")
        
        # Validate warehouse is active
        stock_movement = None
        if hasattr(self.item, 'stock_movement') and self.item.stock_movement_id:
            try:
                stock_movement = self.item.stock_movement
            except self.item.stock_movement.RelatedObjectDoesNotExist:
                if self.item.stock_movement_id:
                    from inventory.models.stock_movement import StockMovement
                    stock_movement = StockMovement.objects.get(id=self.item.stock_movement_id)
        
        if (stock_movement and 
            stock_movement.warehouse and
            hasattr(stock_movement.warehouse, 'is_active')):
            if not stock_movement.warehouse.is_active:
                errors.append("Cannot move items to/from inactive warehouse")
        
        # Validate note length
        if self.item.note and len(self.item.note) > 500:
            errors.append("Note cannot exceed 500 characters")
        
        # Check if item requires special handling
        item_sku = getattr(self.item, 'item_sku', None)
        if (item_sku and 
            hasattr(item_sku, 'requires_temperature_control')):
            if item_sku.requires_temperature_control and not self.item.expiry_date:
                errors.append("Temperature controlled items must have expiry date")
        
        # Movement type consistency
        if not self.item.movement_type:
            errors.append("Movement type is required")
        
        # Stock movement required and status check
        stock_movement = None
        if self.item.stock_movement_id or getattr(self.item, 'stock_movement', None):
            try:
                stock_movement = (getattr(self.item, 'stock_movement', None) 
                                if hasattr(self.item, 'stock_movement') 
                                else None)
                if not stock_movement and self.item.stock_movement_id:
                    from inventory.models.stock_movement import StockMovement
                    stock_movement = StockMovement.objects.get(id=self.item.stock_movement_id)
            except:
                pass
        
        if not stock_movement:
            errors.append("Stock movement is required")
        else:
            # Check if stock movement allows modifications
            from inventory.models.stock_movement import StockMovement
            if stock_movement.status in [
                StockMovement.Status.CONFIRMED,
                StockMovement.Status.PROCESSING,
                StockMovement.Status.COMPLETED,
                StockMovement.Status.FAILED
            ]:
                errors.append("Cannot add items to confirmed or completed stock movements")
        
        return "; ".join(errors) if errors else None


class StockMovementItemImmutableFieldValidator:
    """Validator to prevent modification of critical fields during updates"""
    
    def __init__(self, stock_movement_item):
        self.item = stock_movement_item
    
    def validate(self):
        """Validate that critical fields are not modified during updates"""
        # Only validate during updates (when item has a pk)
        if not self.item.pk:
            return None
            
        try:
            # Get the original item from database
            from inventory.models.stock_movement_item import StockMovementItem
            original = StockMovementItem.objects.get(pk=self.item.pk)
            
            errors = []
            
            # Check if critical fields have been modified
            if self.item.stock_movement_id != original.stock_movement_id:
                errors.append("Stock movement cannot be changed after creation")
                
            if self.item.item_sku_id != original.item_sku_id:
                errors.append("Item SKU cannot be changed after creation")
                
            if self.item.movement_type != original.movement_type:
                errors.append("Movement type cannot be changed after creation")
            
            return "; ".join(errors) if errors else None
            
        except Exception:
            # If we can't get original, skip validation (likely during creation)
            return None
