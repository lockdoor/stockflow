"""
Item Validators

This module contains validators for the ItemSKU model.
Implements business rules and field validation logic.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError
from common.validators.base import BaseValidator


class ItemSKUValidator(BaseValidator):
    """Validator for item SKU field"""
    
    def validate(self):
        """Validate SKU code"""
        errors = []
        
        # Check if SKU is provided
        if not self.instance.sku_code or not self.instance.sku_code.strip():
            errors.append("SKU code is required.")
            return errors
        
        # Normalize SKU code
        sku_code = self.instance.sku_code.strip()
        
        # Check for duplicate SKU (case insensitive)
        from catalog.models.item import ItemSKU
        existing_qs = ItemSKU.objects.filter(sku_code__iexact=sku_code)
        if self.instance.pk:
            existing_qs = existing_qs.exclude(pk=self.instance.pk)
        
        if existing_qs.exists():
            errors.append(f"Item with SKU '{sku_code}' already exists.")
        
        return errors


class ItemNameValidator(BaseValidator):
    """Validator for item name field"""
    
    def validate(self):
        """Validate item name"""
        errors = []
        
        # Check if name is provided
        if not self.instance.name or not self.instance.name.strip():
            errors.append("Item name is required.")
            return errors
        
        # Normalize name
        name = self.instance.name.strip()
        
        # Check length
        if len(name) < 2:
            errors.append("Item name must be at least 2 characters long.")
        
        if len(name) > 100:
            errors.append("Item name cannot exceed 100 characters.")
        
        return errors


class ItemUnitValidator(BaseValidator):
    """Validator for item unit field"""
    
    def validate(self):
        """Validate item unit"""
        errors = []
        
        # Check if unit is provided
        if not self.instance.unit or not self.instance.unit.strip():
            errors.append("Unit is required.")
            return errors
        
        # Normalize unit
        unit = self.instance.unit.strip()
        
        # Check length
        if len(unit) > 20:
            errors.append("Unit cannot exceed 20 characters.")
        
        return errors


class ItemCategoryValidator(BaseValidator):
    """Validator for item category field"""
    
    def validate(self):
        """Validate item category"""
        errors = []
        
        # Check if category exists and is active
        if self.instance.category_id:
            try:
                from catalog.models.category import Category
                category = Category.objects.get(pk=self.instance.category_id)
                if not category.is_active:
                    errors.append("Cannot assign item to inactive category.")
            except Category.DoesNotExist:
                errors.append("Selected category does not exist.")
        
        return errors


class ItemBusinessRulesValidator(BaseValidator):
    """Validator for item business rules"""
    
    def validate(self):
        """Validate item business rules"""
        errors = []
        
        # Validate status based on item type
        if (self.instance.type == self.instance.Type.RAW and 
            self.instance.status == self.instance.Status.DRAFT):
            errors.append(
                "Raw materials cannot be in DRAFT status since they don't have BOMs."
            )
        
        # Validate that status is appropriate for new items
        if hasattr(self.instance, '_state') and self.instance._state.adding:
            # For new RAW materials, recommend ACTIVE status
            if (self.instance.type == self.instance.Type.RAW and 
                self.instance.status == self.instance.Status.INACTIVE):
                errors.append(
                    "New raw materials should typically be ACTIVE. Use INACTIVE only if intentional."
                )
            
            # For new PRODUCT/PACKAGE, recommend DRAFT status
            if (self.instance.type in [self.instance.Type.PRODUCT, self.instance.Type.PACKAGE] and 
                self.instance.status == self.instance.Status.ACTIVE):
                errors.append(
                    f"New {self.instance.type.lower()}s should typically start as DRAFT to allow BOM editing. "
                    f"Use ACTIVE only if BOM is already finalized."
                )
        
        # Validate update operations
        if hasattr(self.instance, '_state') and self.instance._state.adding is False:
            errors.extend(self._validate_update_rules())
        
        return errors
    
    def _validate_update_rules(self):
        """Validate business rules for updates"""
        errors = []
        
        try:
            from catalog.models.item import ItemSKU
            old = ItemSKU.objects.get(pk=self.instance.pk)
        except ItemSKU.DoesNotExist:
            errors.append("Item no longer exists.")
            return errors
        
        # Prevent changing item type once set
        if self.instance.type != old.type:
            errors.append("Item type cannot be changed once set.")
        
        # Prevent changing SKU code once set
        if self.instance.sku_code != old.sku_code:
            errors.append("SKU code cannot be changed once set.")
        
        # Draft status specific rules
        if (old.status in [self.instance.Status.ACTIVE, self.instance.Status.INACTIVE] and 
            self.instance.status == self.instance.Status.DRAFT):
            # Check for BOM dependencies
            # In a real implementation, check if this item is used in other BOMs
            # if BOM.objects.filter(component_sku=self).exists():
            #     errors.append(
            #         "Cannot change to DRAFT status: Item is used as a component in other BOMs."
            #     )
            pass
        
        return errors
