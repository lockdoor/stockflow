# catalog/models/item.py

from django.db import models
from django.core.exceptions import ValidationError
from catalog.models.category import Category
from common.mixins.auditable import AuditableMixin
from catalog.mixins.item_status import ItemStatusMixin
from common.mixins.validatable import ValidatableMixin
from catalog.validators.item_validators import (
    ItemSKUValidator,
    ItemNameValidator,
    ItemUnitValidator,
    ItemCategoryValidator,
    ItemBusinessRulesValidator
)


class ItemSKU(AuditableMixin, ItemStatusMixin, ValidatableMixin, models.Model):
    """
    Item SKU model for managing inventory items with different types and statuses.
    Uses mixins for audit fields, status management, and validation.
    """
    
    class Type(models.TextChoices):
        RAW = 'RAW', 'Raw Material'
        PRODUCT = 'PRODUCT', 'Finished Product'
    
    # Core fields
    sku_code = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique identifier for the item"
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name for the item"
    )
    unit = models.CharField(
        max_length=20,
        help_text="Unit of measurement (e.g., 'pcs', 'kg', 'liters')"
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.RAW,
        help_text="Type of item - cannot be changed once set"
    )
    note = models.TextField(
        blank=True,
        default='',
        help_text="Additional notes about the item"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='items',
        help_text="Category this item belongs to"
    )

    class Meta:
        db_table = 'catalog_itemsku'
        verbose_name = 'Item SKU'
        verbose_name_plural = 'Item SKUs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku_code']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.sku_code} - {self.name}"
    
    def __repr__(self):
        item = f"ItemSKU(sku_code={self.sku_code}, name={self.name}, unit={self.unit}, category={self.category}, created_by={self.created_by}, updated_by={self.updated_by}, type={self.type}, status={self.status})"

        if self.has_bom:
            item += "\nComponents:"
            boms = self.bom_parent.all()
            for bom in boms:
                item += f"\n{bom}"
        return item

    def get_validators(self):
        """Return list of validators for this item"""
        return [
            ItemSKUValidator(self),
            ItemNameValidator(self),
            ItemUnitValidator(self),
            ItemCategoryValidator(self),
            ItemBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """Save with validation and field normalization"""
        # Normalize fields
        if self.sku_code:
            self.sku_code = self.sku_code.strip()
        if self.name:
            self.name = self.name.strip()
        if self.unit:
            self.unit = self.unit.strip()
            
        # Run validation through mixins
        self.full_clean()
        
        # Call parent save (includes optimistic locking)
        super().save(*args, **kwargs)

    @property
    def can_have_bom(self) -> bool:
        """
        Check if this item can have a BOM (Bill of Materials)
        Only PRODUCT types can have a BOM structure
        """
        return self.type == self.Type.PRODUCT

    @property
    def can_be_component(self) -> bool:
        """
        Check if this item can be used as a component in other BOMs
        """
        return True  # All items can be components

    @property
    def is_active(self) -> bool:
        """Check if this item is active"""
        return self.status == self.Status.ACTIVE
    
    @property
    def is_draft(self) -> bool:
        """Check if this item is in draft status"""
        return self.status == self.Status.DRAFT
    
    @property
    def is_inactive(self) -> bool:
        """Check if this item is inactive"""
        return self.status == self.Status.INACTIVE

    @property
    def has_bom(self) -> bool:
        """Check if this item has any BOM components"""
        if not self.can_have_bom:
            return False
        # Use the correct related_name from BOM model
        return hasattr(self, 'bom_parent') and self.bom_parent.exists()

    @property
    def bom_count(self) -> int:
        """Get the count of BOM components for this item"""
        if not self.can_have_bom:
            return 0
        return self.bom_parent.count()

    def get_display_type(self):
        """Get human-readable type display"""
        return self.get_type_display()
    
    def has_primary_image(self):
        """Check if this item has a primary image"""
        return self.images.filter(is_primary=True).exists()

    def get_bom_components(self):
        """Get all BOM components for this item"""
        if not self.can_have_bom:
            raise ValueError("This item type cannot have a BOM.")
        return self.bom_parent.all()

    @classmethod
    def get_active(cls):
        """Get all active items"""
        return cls.objects.filter(status=cls.Status.ACTIVE)
    
    @classmethod
    def get_draft(cls):
        """Get all draft items"""
        return cls.objects.filter(status=cls.Status.DRAFT)
    
    def get_display_name(self):
        """Get formatted display name"""
        return f"{self.sku_code} - {self.name}"
    
    def can_be_deleted(self):
        """
        Check if this item can be deleted (not referenced by other entities)
        Returns tuple (can_delete: bool, blocking_references: list)
        """
        blocking_references = []
        
        # Check if item is used in any BOMs as parent
        if hasattr(self, 'bom_parent') and self.bom_parent.exists():
            blocking_references.append({
                'type': 'BOM (as parent)',
                'count': self.bom_parent.count(),
                'description': 'This item has BOM components'
            })
        
        # Check if item is used in any BOMs as component
        if hasattr(self, 'bom_component') and self.bom_component.exists():
            blocking_references.append({
                'type': 'BOM (as component)',
                'count': self.bom_component.count(),
                'description': 'This item is used as a component in other BOMs'
            })
        
        # Check if item has stock movements
        try:
            if hasattr(self, 'stockmovementitem_set') and self.stockmovementitem_set.exists():
                blocking_references.append({
                    'type': 'Stock Movements',
                    'count': self.stockmovementitem_set.count(),
                    'description': 'This item has stock movement history'
                })
        except Exception:
            pass  # Table might not exist or other database issues
        
        # Check if item has stock records
        try:
            if hasattr(self, 'stocks') and self.stocks.exists():
                blocking_references.append({
                    'type': 'Stock Records',
                    'count': self.stocks.count(),
                    'description': 'This item has current stock records'
                })
        except Exception:
            pass  # Table might not exist or other database issues
        
        # Check if item has production results
        try:
            from django.apps import apps
            if apps.is_installed('production'):
                ProductionResult = apps.get_model('production', 'ProductionResult')
                production_results = ProductionResult.objects.filter(item_sku=self)
                if production_results.exists():
                    blocking_references.append({
                        'type': 'Production Results',
                        'count': production_results.count(),
                        'description': 'This item has production result records'
                    })
        except Exception:
            pass  # Production app not available or table doesn't exist
        
        # Check if item has material reservations
        try:
            if hasattr(self, 'material_reservations') and self.material_reservations.exists():
                blocking_references.append({
                    'type': 'Material Reservations',
                    'count': self.material_reservations.count(), 
                    'description': 'This item has material reservation records'
                })
        except Exception:
            pass  # Table might not exist or other database issues
        
        # Check if item has stock alerts
        try:
            if hasattr(self, 'stock_alerts') and self.stock_alerts.exists():
                blocking_references.append({
                    'type': 'Stock Alerts',
                    'count': self.stock_alerts.count(),
                    'description': 'This item has stock alert records'
                })
        except Exception:
            pass  # Table might not exist or other database issues
        
        can_delete = len(blocking_references) == 0
        return can_delete, blocking_references
