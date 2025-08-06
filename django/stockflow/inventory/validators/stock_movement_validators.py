"""
Stock Movement Validators

Validation logic for StockMovement model, containing business rules
and constraints specific to stock movement operations.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError


class StockMovementStatusValidator:
    """Validator for stock movement status transitions"""
    
    def __init__(self, stock_movement_instance):
        self.stock_movement = stock_movement_instance
    
    def validate(self):
        """Validate status transitions and immutability rules"""
        if not self.stock_movement.pk:
            # New instance, no validation needed
            return None
        
        # Get current state from database
        try:
            current = self.stock_movement.__class__.objects.get(pk=self.stock_movement.pk)
        except self.stock_movement.__class__.DoesNotExist:
            return None
        
        # Confirmed stock movements are immutable
        if current.status == 'CONFIRMED':
            return "Confirmed stock movements cannot be modified"
        
        # Validate status transition
        if not self._is_valid_status_transition(current.status, self.stock_movement.status):
            return f"Invalid status transition from {current.status} to {self.stock_movement.status}"
        
        return None
    
    def _is_valid_status_transition(self, from_status, to_status):
        """Check if status transition is valid"""
        valid_transitions = {
            'DRAFT': ['DRAFT', 'CONFIRMED'],
            'CONFIRMED': []  # No transitions allowed from CONFIRMED
        }
        
        return to_status in valid_transitions.get(from_status, [])


class StockMovementReferenceValidator:
    """Validator for stock movement reference fields"""
    
    def __init__(self, stock_movement_instance):
        self.stock_movement = stock_movement_instance
    
    def validate(self):
        """Validate reference type and reference ID consistency"""
        reference_type = self.stock_movement.reference_type
        reference_id = self.stock_movement.reference_id
        
        # If reference type is NONE, reference_id should be None
        if reference_type == 'NONE' and reference_id is not None:
            return "Reference ID must be empty when reference type is None"
        
        # If reference type is not NONE, reference_id should be provided
        if reference_type != 'NONE' and reference_id is None:
            return f"Reference ID is required when reference type is {reference_type}"
        
        # Validate reference_id is positive
        if reference_id is not None and reference_id <= 0:
            return "Reference ID must be a positive integer"
        
        return None


class StockMovementWarehouseValidator:
    """Validator for stock movement warehouse constraints"""
    
    def __init__(self, stock_movement_instance):
        self.stock_movement = stock_movement_instance
    
    def validate(self):
        """Validate warehouse-related business rules"""
        # Skip validation if warehouse is not set
        if not hasattr(self.stock_movement, 'warehouse') or not self.stock_movement.warehouse:
            return None
            
        warehouse = self.stock_movement.warehouse
        
        # Warehouse must be active for new stock movements
        if not warehouse.is_active and not self.stock_movement.pk:
            return f"Cannot create stock movement for inactive warehouse: {warehouse.name}"
        
        # Check unique draft constraint per warehouse
        if self.stock_movement.status == 'DRAFT':
            existing_draft = self.stock_movement.__class__.objects.filter(
                warehouse=warehouse,
                status='DRAFT'
            ).exclude(pk=self.stock_movement.pk).first()
            
            if existing_draft:
                return f"Warehouse {warehouse.name} already has a draft stock movement (ID: {existing_draft.id})"
        
        return None


class StockMovementBusinessRulesValidator:
    """Validator for general stock movement business rules"""
    
    def __init__(self, stock_movement_instance):
        self.stock_movement = stock_movement_instance
    
    def validate(self):
        """Validate general business rules"""
        errors = []
        
        # Note length validation
        if self.stock_movement.note and len(self.stock_movement.note) > 1000:
            errors.append("Note cannot exceed 1000 characters")
        
        # Validate required fields for confirmation
        if self.stock_movement.status == 'CONFIRMED':
            confirmation_errors = self._validate_confirmation_requirements()
            if confirmation_errors:
                errors.extend(confirmation_errors)
        
        return "; ".join(errors) if errors else None
    
    def _validate_confirmation_requirements(self):
        """Validate requirements for confirming stock movement"""
        errors = []
        
        # Must have at least one stock movement item
        if hasattr(self.stock_movement, 'movement_items'):
            if not self.stock_movement.movement_items.exists():
                errors.append("Cannot confirm stock movement without items")
        
        # All items must have valid quantities
        if hasattr(self.stock_movement, 'movement_items'):
            for item in self.stock_movement.movement_items.all():
                if item.quantity <= 0:
                    errors.append(f"Item {item.item_sku} has invalid quantity: {item.quantity}")
        
        return errors


class StockMovementVersionValidator:
    """Validator for optimistic locking using version field"""
    
    def __init__(self, stock_movement_instance):
        self.stock_movement = stock_movement_instance
    
    def validate(self):
        """Validate version for optimistic locking"""
        if not self.stock_movement.pk:
            # New instance, no validation needed
            return None
        
        try:
            current = self.stock_movement.__class__.objects.get(pk=self.stock_movement.pk)
            if current.version != self.stock_movement.version:
                return "Record has been modified by another user. Please refresh and try again."
        except self.stock_movement.__class__.DoesNotExist:
            return "Record no longer exists"
        
        return None
