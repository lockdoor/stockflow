"""
BOM Validators

This module contains validators for the BOM (Bill of Materials) model.
Implements business rules and field validation logic for BOM relationships.

Author: StockFlow Team
"""

from decimal import Decimal
from common.validators.base import BaseValidator


class BOMParentSKUValidator(BaseValidator):
    """Validator for BOM parent SKU field"""
    
    def validate(self):
        """Validate parent SKU"""
        errors = []
        
        if not self.instance.parent_sku_id:
            errors.append("Parent SKU is required")
            return errors
            
        # Check if parent status allows BOM editing - only for new BOMs
        # Allow updates to existing BOMs even if parent is locked
        if not self.instance.pk and hasattr(self.instance.parent_sku, 'is_bom_locked') and self.instance.parent_sku.is_bom_locked():
            errors.append("Cannot create new BOM when parent item is locked")
            
        return errors


class BOMComponentSKUValidator(BaseValidator):
    """Validator for BOM component SKU field"""
    
    def validate(self):
        """Validate component SKU"""
        errors = []
        
        if not self.instance.component_sku_id:
            errors.append("Component SKU is required")
            return errors
               
        # Check for self-reference
        if self.instance.parent_sku_id and self.instance.component_sku_id:
            if self.instance.parent_sku_id == self.instance.component_sku_id:
                errors.append("A product cannot be its own component")
                
        # Component must be ACTIVE
        if self.instance.component_sku.status != 'ACTIVE':
            errors.append("Only ACTIVE components can be used in BOM")
            
        return errors


class BOMQuantityValidator(BaseValidator):
    """Validator for BOM quantity field"""
    
    def validate(self):
        """Validate quantity is positive"""
        errors = []
        
        if self.instance.quantity is None:
            errors.append("Quantity is required")
        elif self.instance.quantity <= 0:
            errors.append("Quantity must be greater than zero")
            
        return errors


class BOMDuplicateValidator(BaseValidator):
    """Validator for preventing duplicate BOM entries"""
    
    def validate(self):
        """Validate no duplicate BOM entries exist"""
        errors = []
        
        if self.instance.parent_sku_id and self.instance.component_sku_id:
            from catalog.models.bom import BOM
            
            existing = BOM.objects.filter(
                parent_sku=self.instance.parent_sku,
                component_sku=self.instance.component_sku
            )
            
            # Exclude current instance if it's an update
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
                
            if existing.exists():
                errors.append("This component is already in the BOM for this parent item")
                
        return errors


class BOMCircularReferenceValidator(BaseValidator):
    """Validator for BOM circular reference prevention"""
    
    def validate(self):
        """Validate no circular references would be created"""
        errors = []
        
        if self.instance.parent_sku_id and self.instance.component_sku_id:
            from catalog.models.bom import BOM
            
            # Skip validation for existing unchanged relationships
            if self.instance.pk:
                try:
                    original = BOM.objects.get(pk=self.instance.pk)
                    if (original.parent_sku_id == self.instance.parent_sku_id and 
                        original.component_sku_id == self.instance.component_sku_id):
                        # Relationship hasn't changed, skip validation
                        return errors
                except BOM.DoesNotExist:
                    pass
                
            if BOM.has_circular_reference(self.instance.parent_sku, self.instance.component_sku):
                errors.append("Adding this component would create a circular reference in the BOM structure")
                
        return errors


class BOMBusinessRulesValidator(BaseValidator):
    """Validator for BOM business rules and constraints"""
    
    def validate(self):
        """Validate business rules"""
        errors = []
        
        # Additional business rules can be added here
        # For example: maximum BOM depth, component type restrictions, etc.
        
        # Validate audit fields are set (if instance has them)
        if hasattr(self.instance, 'created_by') and not self.instance.created_by:
            errors.append("Created by user is required")
            
        if hasattr(self.instance, 'updated_by') and not self.instance.updated_by:
            errors.append("Updated by user is required")
        
        return errors
