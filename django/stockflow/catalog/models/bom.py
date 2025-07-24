from django.db import models
from django.core.exceptions import ValidationError
from catalog.models.item import ItemSKU
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User
from decimal import Decimal


class BOM(models.Model):
    """
    Bill of Materials model representing the components needed to build an item.
    Provides full business logic validation and state management.
    """
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
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='bom_created_by',
        help_text="User who created this BOM"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='bom_updated_by',
        help_text="User who last updated this BOM"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(
        default=0,
        help_text="Version number for optimistic locking"
    )
    history = HistoricalRecords()
    
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

    def __str__(self):
        return f"{self.parent_sku.sku_code} needs {self.quantity} x {self.component_sku.sku_code}"

    # Private validation methods
    def _validate_parent_sku(self) -> str | None:
        """
        Validate parent SKU is suitable for a BOM (not a raw material)
        """
        if not self.parent_sku_id:
            return "Parent SKU is required"
            
        if self.parent_sku.type == ItemSKU.Type.RAW:
            return "Cannot create BOM with parent SKU as a raw material"
            
        if self.parent_sku.is_bom_locked():
            return "Cannot modify BOM when parent item is not in DRAFT status"
        
        return None
        
    def _validate_component_sku(self) -> str | None:
        """
        Validate component SKU
        """
        if not self.component_sku_id:
            return "Component SKU is required"
               
        if self.parent_sku_id and self.component_sku_id:
            if self.parent_sku_id == self.component_sku_id:
                return "Parent SKU and component SKU cannot be the same"

        if not self.component_sku.is_active():
            return "Component SKU must be active"
                
        return None
        
    def _validate_quantity(self) -> str | None:
        """
        Validate quantity is positive
        """
        if not self.quantity:
            return "Quantity is required"
            
        if self.quantity <= Decimal('0'):
            return "Quantity must be greater than zero"
            
        return None
        
    def _validate_duplicate_component(self) -> str | None:
        """
        Validate no duplicate components in the same BOM
        """
        if not self.pk and self.parent_sku_id and self.component_sku_id:
            if BOM.objects.filter(parent_sku=self.parent_sku, component_sku=self.component_sku).exists():
                return "This component already exists in the BOM"
                
        return None

    def clean(self):
        """
        Model-level validation - handles business logic validation
        Calls individual validation methods for each field
        Raises ValidationError for business logic violations
        """
        errors = []
        
        # Call field-specific validation methods
        field_validations = [
            self._validate_parent_sku(),
            self._validate_component_sku(),
            self._validate_quantity(),
            self._validate_duplicate_component()
        ]
        
        # Add non-None validation errors
        errors.extend([error for error in field_validations if error])
        
        if errors:
            raise ValidationError("; ".join(errors))

    def save(self, *args, **kwargs):
        """
        Override save method to handle business logic and validation
        """
        try:
            # Run model validation first
            self.full_clean()

            if self.pk:  # Updating existing BOM
                self._handle_optimistic_locking()
            
            super().save(*args, **kwargs)
            
        except ValidationError as e:
            # Convert ValidationError to ValueError for consistency with our error handling approach
            # This ensures business logic validation errors are consistently returned as ValueError
            # while keeping Django's form validation flow intact (using ValidationError in clean())
            if hasattr(e, 'message_dict'):
                error_messages = []
                for field, messages in e.message_dict.items():
                    if isinstance(messages, list):
                        error_messages.extend(messages)
                    else:
                        error_messages.append(str(messages))
                raise ValueError("; ".join(error_messages))
            else:
                raise ValueError(str(e))
            
        except Exception as e:
            # Handle other exceptions
            raise ValueError(str(e))
            
    def _handle_optimistic_locking(self):
        """
        Handle optimistic locking to prevent concurrent updates
        """
        try:
            current = BOM.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValueError("Optimistic locking failed: BOM record has been modified by another user")
            self.version += 1
        except BOM.DoesNotExist:
            raise ValueError("BOM record no longer exists")
            
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
            
        # Check if the component uses the parent in its own BOM (recursively)
        visited = set()
        to_check = [component_sku.id]
        
        while to_check:
            current_id = to_check.pop()
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            # If we find the parent in the component's BOM tree, it's circular
            if current_id == parent_sku.id:
                return True
                
            # Add all components of the current item to check
            component_parents = cls.objects.filter(component_sku_id=current_id).values_list('parent_sku_id', flat=True)
            to_check.extend([pid for pid in component_parents if pid not in visited])
            
        return False
