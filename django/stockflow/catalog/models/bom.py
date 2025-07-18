# catalog/models/bom.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from catalog.models.item import ItemSKU
from simple_history.models import HistoricalRecords


class BOM(models.Model):
    """
    Bill of Materials (BOM) model for managing component relationships.
    Defines what components are needed to build a finished product or package.
    Includes business logic for validation and state management.
    """
    
    # Core fields
    parent_sku = models.ForeignKey(
        ItemSKU, 
        on_delete=models.CASCADE, 
        related_name='bom_parent',
        help_text="Parent item that contains the components"
    )
    component_sku = models.ForeignKey(
        ItemSKU, 
        on_delete=models.PROTECT, 
        related_name='bom_component',
        help_text="Component item used in the parent"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Quantity of component needed for one unit of parent"
    )
    
    # Versioning for concurrency control
    version = models.PositiveIntegerField(
        default=0,
        help_text="Version number for optimistic locking"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='bom_created',
        help_text="User who created this BOM entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='bom_updated',
        help_text="User who last updated this BOM entry"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # History tracking
    history = HistoricalRecords()

    class Meta:
        db_table = 'catalog_bom'
        verbose_name = 'Bill of Materials'
        verbose_name_plural = 'Bills of Materials'
        ordering = ['parent_sku__sku_code', 'component_sku__sku_code']
        unique_together = [['parent_sku', 'component_sku']]
        indexes = [
            models.Index(fields=['parent_sku']),
            models.Index(fields=['component_sku']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.parent_sku.sku_code} needs {self.quantity} x {self.component_sku.sku_code}"
    
    def _validate_parent_sku(self) -> str | None:
        """
        Validate parent SKU can have a BOM
        """
        if not self.parent_sku_id:
            return "Parent SKU is required"
            
        try:
            parent = ItemSKU.objects.get(pk=self.parent_sku_id)
            if not parent.can_have_bom():
                return f"Parent SKU type '{parent.get_display_type()}' cannot have a BOM"
        except ItemSKU.DoesNotExist:
            return "Selected parent SKU does not exist"
        
        return None
        
    def _validate_component_sku(self) -> str | None:
        """
        Validate component SKU exists and can be used as component
        """
        if not self.component_sku_id:
            return "Component SKU is required"
            
        try:
            component = ItemSKU.objects.get(pk=self.component_sku_id)
            if not component.can_be_component():
                return "Selected component SKU cannot be used as a component"
        except ItemSKU.DoesNotExist:
            return "Selected component SKU does not exist"
        
        return None
        
    def _validate_quantity(self) -> str | None:
        """
        Validate quantity is positive
        """
        if self.quantity is None:
            return "Quantity is required"
        if self.quantity <= 0:
            return "Quantity must be greater than zero"
        return None
        
    def _validate_self_reference(self) -> str | None:
        """
        Validate parent and component are not the same
        """
        if self.parent_sku_id and self.component_sku_id and self.parent_sku_id == self.component_sku_id:
            return "Parent SKU and component SKU cannot be the same"
        
        return None
  
    def _validate_self_reference_recursive(self) -> str | None:
        """
        Validate that the BOM does not create a recursive relationship
        """
        def _check_recursive_target(parent_sku, target_sku_id, visited=None) -> bool:
            """
            Recursively check if target_sku_id appears in any component hierarchy
            """
            if visited is None:
                visited = set()
                
            # Prevent infinite loops
            if parent_sku.id in visited:
                return False
            visited.add(parent_sku.id)
            
            # Get all components for this parent
            components = BOM.objects.filter(parent_sku=parent_sku).select_related('component_sku')
            
            for component in components:
                # If we find the target in components, it's a cycle
                if component.component_sku.id == target_sku_id:
                    return True
                    
                # If component can have BOM, check its components recursively
                if component.component_sku.can_have_bom():
                    if _check_recursive_target(component.component_sku, target_sku_id, visited.copy()):
                        return True
            
            return False
            
        if self.parent_sku_id and self.component_sku_id:
            try:
                # For new BOM entries, check if adding this component would create a cycle
                # We need to check if the component (when it becomes a parent) 
                # would eventually contain the current parent as a component
                component = ItemSKU.objects.get(pk=self.component_sku_id)
                if component.can_have_bom():
                    if _check_recursive_target(component, self.parent_sku_id):
                        return "Recursive relationship detected in BOM structure"
                        
            except ItemSKU.DoesNotExist:
                return "Component SKU does not exist"
                
        return None
        
    def _validate_duplicate_component(self) -> str | None:
        """
        Validate component is not already in this parent's BOM
        """
        if not self.pk and self.parent_sku_id and self.component_sku_id:
            if BOM.objects.filter(parent_sku_id=self.parent_sku_id, component_sku_id=self.component_sku_id).exists():
                return "This component already exists in the BOM"
        return None
        
    def _validate_bom_locked(self) -> str | None:
        """
        Validate BOM is not locked for editing
        """
        if self.parent_sku_id:
            try:
                parent = ItemSKU.objects.get(pk=self.parent_sku_id)
                if parent.is_bom_locked():
                    return "Cannot modify BOM when parent item is locked (not in DRAFT status)"
            except ItemSKU.DoesNotExist:
                return "Parent SKU does not exist"
        return None

    def clean(self):
        """
        Model-level validation - handles business logic validation
        Calls individual validation methods for each field
        Raises ValidationError for business logic violations which will be converted to ValueError in save()
        """
        errors = []
        
        # Call field-specific validation methods
        field_validations = [
            self._validate_parent_sku(),
            self._validate_component_sku(),
            self._validate_quantity(),
            self._validate_self_reference(),
            self._validate_self_reference_recursive(),
            self._validate_duplicate_component(),
            self._validate_bom_locked()
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
                self._validate_update()
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
            
        except ValueError as e:
            # Handle business logic validation errors
            raise ValueError(str(e))

    def _validate_update(self):
        """
        Validate update operations - business logic for existing BOM entries
        """
        try:
            old = BOM.objects.get(pk=self.pk)
        except BOM.DoesNotExist:
            raise ValueError("BOM entry no longer exists")
        
        # Prevent changing parent/component relationship once set
        if self.parent_sku_id != old.parent_sku_id:
            raise ValueError("Parent SKU cannot be changed once set")
        if self.component_sku_id != old.component_sku_id:
            raise ValueError("Component SKU cannot be changed once set")

    def _handle_optimistic_locking(self):
        """
        Handle optimistic locking to prevent concurrent updates
        """
        try:
            current = BOM.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValueError("The BOM entry has been modified by another user. Please refresh and try again")
            self.version += 1
        except BOM.DoesNotExist:
            raise ValueError("BOM entry no longer exists")

    # Business logic methods
    def can_modify(self):
        """
        Check if this BOM entry can be modified
        """
        return not self.parent_sku.is_bom_locked()
        
    def can_delete(self):
        """
        Check if this BOM entry can be deleted
        """
        return not self.parent_sku.is_bom_locked()
        
    def get_total_cost(self):
        """
        Calculate total cost for this BOM line item
        Note: This would require a cost field on ItemSKU in a real implementation
        """
        # In a real implementation, you would calculate:
        # return self.quantity * self.component_sku.unit_cost
        return None
        
    def get_component_display(self):
        """
        Get formatted display string for the component
        """
        return f"{self.quantity} x {self.component_sku.sku_code} ({self.component_sku.name})"
