"""
BOM (Bill of Materials) Model

This module defines the BOM model using mixins for clean separation of concerns.
Uses AuditableMixin for audit fields and optimistic locking,
and ValidatableMixin for validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from catalog.models.item import ItemSKU
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin
from catalog.validators.bom_validators import (
    BOMParentSKUValidator,
    BOMComponentSKUValidator,
    BOMQuantityValidator,
    BOMDuplicateValidator,
    BOMCircularReferenceValidator,
    BOMBusinessRulesValidator
)
from decimal import Decimal


class BOM(AuditableMixin, ValidatableMixin, models.Model):
    """
    Bill of Materials model representing the components needed to build an item.
    Uses mixins for audit fields and validation framework.
    """
    
    # Core fields
    parent_sku = models.ForeignKey(
        ItemSKU, 
        on_delete=models.CASCADE, 
        related_name='bom_parent',
        help_text="The item that this BOM belongs to"
    )
    component_sku = models.ForeignKey(
        ItemSKU, 
        on_delete=models.PROTECT, 
        related_name='bom_component',
        help_text="The component used in this BOM"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Quantity of the component required"
    )
    
    class Meta:
        db_table = 'catalog_bom'
        verbose_name = 'BOM'
        verbose_name_plural = 'BOMs'
        unique_together = [['parent_sku', 'component_sku']]
        indexes = [
            models.Index(fields=['parent_sku']),
            models.Index(fields=['component_sku']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.parent_sku.sku_code} needs {self.quantity} x {self.component_sku.sku_code}"

    def get_validators(self):
        """Return list of validators for this BOM"""
        return [
            BOMParentSKUValidator(self),
            BOMComponentSKUValidator(self),
            BOMQuantityValidator(self),
            BOMDuplicateValidator(self),
            BOMCircularReferenceValidator(self),
            BOMBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """Save with validation and field normalization"""
        # Run validation through mixins
        self.full_clean()
        
        # Call parent save (includes optimistic locking)
        super().save(*args, **kwargs)
    # Business logic methods
    def is_active(self):
        """
        Check if both parent and component are active
        """
        return self.parent_sku.is_active() and self.component_sku.is_active()
    
    def can_be_modified(self):
        """
        Check if this BOM can be modified
        BOM can only be modified if the parent item is in DRAFT status
        """
        return not self.parent_sku.is_bom_locked()
        
    def can_be_deleted(self):
        """
        Check if this BOM can be deleted
        BOM can only be deleted if the parent item is in DRAFT status
        """
        return not self.parent_sku.is_bom_locked()
    
    # Manager methods
    @classmethod
    def get_components_for_item(cls, item_sku):
        """
        Get all BOM components for a given item
        """
        return cls.objects.filter(parent_sku=item_sku).select_related('component_sku')
    
    @classmethod
    def get_items_using_component(cls, component_sku):
        """
        Get all items that use a specific component in their BOM
        """
        return cls.objects.filter(component_sku=component_sku).select_related('parent_sku')
        
    @classmethod
    def has_circular_reference(cls, parent_sku, component_sku):
        """
        Check for circular references in BOM structure
        Returns True if adding component_sku to parent_sku's BOM would create a circular reference
        """
        # If they are the same, it's definitely circular
        if parent_sku.id == component_sku.id:
            return True
            
        # Check if the parent uses the component in its own BOM tree (forward check)
        # If component is already a parent of our parent, then adding parent as component's component would create cycle
        visited = set()
        to_check = [parent_sku.id]
        
        while to_check:
            current_id = to_check.pop()
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            # Get all components of the current item
            component_ids = cls.objects.filter(parent_sku_id=current_id).values_list('component_sku_id', flat=True)
            
            for comp_id in component_ids:
                # If we find the component we're trying to add in the parent's BOM tree, it's circular
                if comp_id == component_sku.id:
                    return True
                    
                # Add this component to check its own components
                if comp_id not in visited:
                    to_check.append(comp_id)
            
        return False
