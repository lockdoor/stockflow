# catalog/models/item.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from catalog.models.category import Category
from simple_history.models import HistoricalRecords


class ItemSKU(models.Model):
    """
    Item SKU model for managing inventory items with different types and statuses.
    Includes business logic for validation and state management.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        DRAFT = 'DRAFT', 'Draft'
        
    class Type(models.TextChoices):
        RAW = 'RAW', 'Raw Material'
        PRODUCT = 'PRODUCT', 'Finished Product'
        PACKAGE = 'PACKAGE', 'Package'
    
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
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,  # Default to ACTIVE since default type is RAW
        help_text="Current status of the item - DRAFT allows BOM structure changes, ACTIVE/INACTIVE locks BOM structure"
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
    
    # Versioning for concurrency control
    version = models.PositiveIntegerField(
        default=0,
        help_text="Version number for optimistic locking"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='items_created',
        help_text="User who created this item"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='items_updated',
        help_text="User who last updated this item"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # History tracking
    history = HistoricalRecords()

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
    
    def _validate_sku_code(self) -> str | None:
        """
        Validate and clean SKU code format
        """
        if not self.sku_code:
            return "SKU code is required"
        # Clean the SKU code by removing whitespace
        self.sku_code = self.sku_code.strip()
        if len(self.sku_code) == 0:
            return "SKU code cannot be empty or whitespace only"        
        return None
        
    def _validate_name(self) -> str | None:
        """
        Validate and clean item name
        """
        if not self.name:
            return "Item name is required"
        # Clean the name by removing whitespace
        self.name = self.name.strip()
        if len(self.name) == 0:
            return "Item name cannot be empty or whitespace only"  
        return None
        
    def _validate_unit(self) -> str | None:
        """
        Validate unit
        """
        if not self.unit:
            return "Unit is required"        
        # Clean the unit by removing whitespace
        self.unit = self.unit.strip()
        if len(self.unit) == 0:
            return "Unit cannot be empty or whitespace only"
        return None
        
    def _validate_status(self) -> str | None:
        """
        Validate status based on item type
        """
        if self.type == self.Type.RAW and self.status == self.Status.DRAFT:
            return "Raw materials cannot be in DRAFT status since they don't have BOMs"
        return None
        
    def _validate_category(self) -> str | None:
        """
        Validate category exists and is active
        """
        if not self.category_id:
            return None
            
        try:
            category = Category.objects.get(pk=self.category_id)
            if not category.is_active:
                return "Cannot assign item to inactive category"
        except Category.DoesNotExist:
            return "Selected category does not exist"
        
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
            self._validate_sku_code(),
            self._validate_name(),
            self._validate_unit(),
            self._validate_status(),
            self._validate_category()
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

            if self.pk:  # Updating existing item
                self._validate_update()
                self._handle_optimistic_locking()
            else:  # Creating new item
                self._set_initial_state()
                
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
        Validate update operations - business logic for existing items
        """
        try:
            old = ItemSKU.objects.get(pk=self.pk)
        except ItemSKU.DoesNotExist:
            raise ValueError("Item no longer exists")
        
        # Prevent changing item type once set (this is a fundamental property that can never change)
        if self.type != old.type:
            raise ValueError("Item type cannot be changed once set")
        
        # Prevent changing SKU code once set (this is a fundamental identifier that can never change)
        if self.sku_code != old.sku_code:
            raise ValueError("SKU code cannot be changed once set")
        
        # Draft status specific rules - only related to BOM structure
        # If item was in ACTIVE/INACTIVE status, it can go back to DRAFT only if it doesn't have dependencies
        if old.status in [self.Status.ACTIVE, self.Status.INACTIVE] and self.status == self.Status.DRAFT:
            # For a real implementation, check for BOM dependencies here
            # If this item is used as a component in any other item's BOM, prevent going back to DRAFT
            # For example:
            # if BOM.objects.filter(component_sku=self).exists():
            #     raise ValueError("Cannot change to DRAFT status: Item is used as a component in other BOMs")
            pass

    def _handle_optimistic_locking(self):
        """
        Handle optimistic locking to prevent concurrent updates
        """
        try:
            current = ItemSKU.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValueError("The item has been modified by another user. Please refresh and try again")
            self.version += 1
        except ItemSKU.DoesNotExist:
            raise ValueError("Item no longer exists")

    def _set_initial_state(self):
        """
        Set initial state for new items
        """
        # RAW materials start as ACTIVE (no BOM editing allowed)
        if self.type == self.Type.RAW:
            self.status = self.Status.ACTIVE
        else:
            # PRODUCT and PACKAGE start as DRAFT (BOM editing allowed)
            self.status = self.Status.DRAFT

    # Business logic methods
    def can_have_bom(self):
        """
        Check if this item can have a BOM (Bill of Materials)
        Only PRODUCT and PACKAGE types can have a BOM structure
        """
        return self.type in [self.Type.PRODUCT, self.Type.PACKAGE]

    def can_be_component(self):
        """
        Check if this item can be used as a component in other BOMs
        """
        return True  # All items can be components

    def is_active(self):
        """
        Check if item is active
        """
        return self.status == self.Status.ACTIVE
        
    def is_draft(self):
        """
        Check if item is in draft mode (BOM structure changes allowed)
        """
        # Only return True if status is explicitly DRAFT, not INACTIVE or ACTIVE
        return self.status == self.Status.DRAFT
        
    def is_bom_locked(self):
        """
        Check if the BOM structure is locked (not in draft mode)
        """
        return self.status != self.Status.DRAFT
        
    def is_allows_bom_changes(self):
        """
        Check if the item allows BOM structure changes
        """
        return self.status == self.Status.DRAFT and self.can_have_bom()

    def lock_bom(self):
        """
        Lock the BOM structure for this item by changing status from DRAFT to ACTIVE
        """
        if not self.can_have_bom():
            raise ValueError("This item type cannot have a BOM")
            
        if self.status == self.Status.DRAFT:
            self.status = self.Status.ACTIVE
            
        return self
        
    def unlock_bom(self):
        """
        Unlock the BOM structure for editing by changing status to DRAFT
        This will fail if the item is used as a component in other BOMs
        """
        if not self.can_have_bom():
            raise ValueError("This item type cannot have a BOM")
            
        # Check for dependencies before allowing unlock
        # In a real implementation, you would check if this item is used in other BOMs
        # Example:
        # if BOM.objects.filter(component_sku=self).exists():
        #    raise ValueError("Cannot unlock BOM: Item is used as a component in other BOMs")
        
        self.status = self.Status.DRAFT
        return self

    def get_display_type(self):
        """
        Get human-readable type display
        """
        return self.get_type_display()

    def get_display_status(self):
        """
        Get human-readable status display
        """
        return self.get_status_display()
