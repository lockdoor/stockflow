"""
Warehouse Validators

Validation logic for Warehouse model, using common base validators
for consistent validation patterns across the application.

Author: StockFlow Team
Created: 2025
"""

from common.validators.base_validators import (
    RequiredFieldValidator,
    LengthValidator,
    UniqueFieldValidator,
    CodeFormatValidator
)


class WarehouseNameValidator:
    """Validator for warehouse name field"""
    
    def __init__(self, warehouse_instance):
        self.warehouse = warehouse_instance
    
    def validate(self):
        """Validate warehouse name using base validators"""
        validators = [
            RequiredFieldValidator(self.warehouse, 'name'),
            LengthValidator(self.warehouse, 'name', min_length=2, max_length=100),
            UniqueFieldValidator(self.warehouse, 'name', case_sensitive=False)
        ]
        
        for validator in validators:
            error = validator.validate()
            if error:
                return error
        
        return None


class WarehouseCodeValidator:
    """Validator for warehouse code field"""
    
    def __init__(self, warehouse_instance):
        self.warehouse = warehouse_instance
    
    def validate(self):
        """Validate warehouse code using base validators"""
        validators = [
            RequiredFieldValidator(self.warehouse, 'code'),
            CodeFormatValidator(self.warehouse, 'code', min_length=2, max_length=10),
            UniqueFieldValidator(self.warehouse, 'code', case_sensitive=False)
        ]
        
        for validator in validators:
            error = validator.validate()
            if error:
                return error
        
        return None


class WarehouseBusinessRulesValidator:
    """Validator for warehouse business rules"""
    
    def __init__(self, warehouse_instance):
        self.warehouse = warehouse_instance
    
    def validate(self):
        """Validate warehouse business rules"""
        validators = [
            LengthValidator(self.warehouse, 'address', max_length=500),
            LengthValidator(self.warehouse, 'note', max_length=1000)
        ]
        
        errors = []
        
        # Run length validators
        for validator in validators:
            error = validator.validate()
            if error:
                errors.append(error)
        
        # Check if warehouse can be deactivated
        if not self.warehouse.is_active:
            can_deactivate, reason = self._check_can_deactivate()
            if not can_deactivate:
                errors.append(f"Cannot deactivate warehouse: {reason}")
        
        return "; ".join(errors) if errors else None
    
    def _check_can_deactivate(self):
        """Check if warehouse can be deactivated"""
        # Check if warehouse has active stock movements
        try:
            from inventory.models.stock_movement import StockMovement
            active_movements = StockMovement.objects.filter(
                warehouse=self.warehouse,
                status=StockMovement.Status.DRAFT
            )
            
            if active_movements.exists():
                return False, "Warehouse has active stock movements"
        except ImportError:
            # StockMovement not available, skip check
            pass
        
        # Check if warehouse has current stock
        # TODO: Add stock level checking when Stock model is implemented
        
        return True, ""
