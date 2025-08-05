"""
Warehouse Model

This module defines the Warehouse model using mixins for clean separation of concerns.
Uses AuditableMixin for audit fields and optimistic locking,
StatusMixin for status management, and ValidatableMixin for validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models, transaction
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from common.mixins.auditable import AuditableMixin
from common.mixins.status import StatusMixin
from common.mixins.validatable import ValidatableMixin
from inventory.validators.warehouse_validators import (
    WarehouseNameValidator,
    WarehouseCodeValidator,
    WarehouseBusinessRulesValidator
)


class Warehouse(AuditableMixin, StatusMixin, ValidatableMixin, models.Model):
    """
    Warehouse model for inventory management.
    
    Represents physical locations where inventory items are stored.
    Includes name, code, address and status management.
    """
    
    # Core fields
    name = models.CharField(
        max_length=100,
        help_text="Warehouse display name"
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Unique warehouse code (2-10 alphanumeric characters)"
    )
    address = models.TextField(
        blank=True, 
        null=True,
        help_text="Physical address of the warehouse"
    )
    note = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes about the warehouse"
    )

    class Meta:
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        """String representation of the warehouse"""
        return f"{self.code} - {self.name}"

    def get_validators(self):
        """Return list of validators for this warehouse"""
        return [
            WarehouseNameValidator(self),
            WarehouseCodeValidator(self),
            WarehouseBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """Save with validation and code normalization"""
        # Normalize code to uppercase
        if self.code:
            self.code = self.code.upper().strip()
        
        # Normalize name
        if self.name:
            self.name = self.name.strip()
        
        # Run validation through mixins
        self.full_clean()
        
        # Check if this is a new warehouse
        is_new = self.pk is None
        
        # Use transaction for new warehouse creation with permissions
        if is_new:
            with transaction.atomic():
                super().save(*args, **kwargs)
                self._create_warehouse_permissions()
        else:
            super().save(*args, **kwargs)

    def _create_warehouse_permissions(self):
        """Create warehouse-specific group and permissions"""
        # สร้าง group สำหรับ warehouse นี้
        group_name = f"warehouse_{self.id}_staff"
        group, _ = Group.objects.get_or_create(name=group_name)

        # สร้าง permission เฉพาะ warehouse
        content_type = ContentType.objects.get_for_model(Warehouse)
        perm_codename = f"can_manage_warehouse_{self.id}"
        perm_name = f"Can manage Warehouse {self.name} (ID {self.id})"
        permission, _ = Permission.objects.get_or_create(
            codename=perm_codename,
            name=perm_name,
            content_type=content_type
        )
        
        # เพิ่ม permission ให้ group
        group.permissions.add(permission)

        # เพิ่ม permission ให้ group superuser ด้วย
        superuser_group, _ = Group.objects.get_or_create(name='superuser')
        superuser_group.permissions.add(permission)

    def can_deactivate(self):
        """Check if warehouse can be deactivated"""
        # Check for active stock movements
        active_movements = self.stock_movements.filter(
            status='DRAFT'
        ).exists()
        
        if active_movements:
            return False, "Warehouse has active stock movements"
        
        # TODO: Check for current stock when Stock model is implemented
        
        return True, ""

    def get_display_name(self):
        """Get formatted display name"""
        return f"{self.code} - {self.name}"

    @property
    def has_stock_movements(self):
        """Check if warehouse has any stock movements"""
        return self.stock_movements.exists()
    
    @property
    def active_movements_count(self):
        """Get count of active (draft) movements"""
        return self.stock_movements.filter(status='DRAFT').count()
