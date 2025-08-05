"""
Item Status Mixin

Provides status management functionality specific to ItemSKU models.
Handles DRAFT, ACTIVE, INACTIVE states and BOM locking logic.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.core.exceptions import ValidationError


class ItemStatusMixin(models.Model):
    """
    Abstract mixin that provides item-specific status management.
    
    Handles DRAFT, ACTIVE, INACTIVE states with BOM locking logic.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        DRAFT = 'DRAFT', 'Draft'
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Current status of the item - DRAFT allows BOM structure changes, ACTIVE/INACTIVE locks BOM structure"
    )
    
    class Meta:
        abstract = True
    
    def is_active(self):
        """Check if item is active"""
        return self.status == self.Status.ACTIVE
        
    def is_draft(self):
        """Check if item is in draft mode (BOM structure changes allowed)"""
        return self.status == self.Status.DRAFT
        
    def is_inactive(self):
        """Check if item is inactive"""
        return self.status == self.Status.INACTIVE
        
    def is_bom_locked(self):
        """Check if the BOM structure is locked (not in draft mode)"""
        return self.status != self.Status.DRAFT
        
    def allows_bom_changes(self):
        """Check if the item allows BOM structure changes"""
        return self.status == self.Status.DRAFT and self.can_have_bom
    
    def lock_bom(self):
        """Lock the BOM structure for this item by changing status from DRAFT to ACTIVE"""
        if not self.can_have_bom:
            raise ValidationError("This item type cannot have a BOM")
            
        if self.status == self.Status.DRAFT:
            self.status = self.Status.ACTIVE
            
        return self
        
    def unlock_bom(self):
        """Unlock the BOM structure for editing by changing status to DRAFT"""
        if not self.can_have_bom:
            raise ValidationError("This item type cannot have a BOM")
            
        # Check for dependencies before allowing unlock
        # In a real implementation, check if this item is used in other BOMs
        # if BOM.objects.filter(component_sku=self).exists():
        #    raise ValidationError("Cannot unlock BOM: Item is used as a component in other BOMs")
        
        self.status = self.Status.DRAFT
        return self
    
    def activate(self):
        """Activate this item"""
        self.status = self.Status.ACTIVE
    
    def deactivate(self):
        """Deactivate this item"""
        self.status = self.Status.INACTIVE
    
    def set_draft(self):
        """Set item to draft status"""
        self.status = self.Status.DRAFT
    
    @property
    def status_display(self):
        """Get human-readable status"""
        return self.get_status_display()
    
    def can_have_bom(self):
        """
        Check if this item can have a BOM (Bill of Materials)
        Override in subclasses to implement specific logic
        """
        return True
    
    def can_be_component(self):
        """
        Check if this item can be used as a component in other BOMs
        Override in subclasses to implement specific logic
        """
        return True
