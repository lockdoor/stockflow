"""
Warehouse Model

This module defines the Warehouse model using mixins for clean separation of concerns.
Uses AuditableMixin for audit fields and optimistic locking,
StatusMixin for status management, and ValidatableMixin for validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models, transaction
from django.contrib.auth.models import Group, Permission, User
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
        """
        Create warehouse-specific group and permissions for inventory and production.
        
        This method creates:
        1. A warehouse-specific group (warehouse_{id}_staff)
        2. 8 permissions for various warehouse operations
        3. Adds all permissions to both warehouse group and superuser group
        4. Automatically adds the warehouse creator to the warehouse group
        
        Returns:
            tuple: (group, list of created permissions)
        """
        from inventory.models import Stock, StockMovement, MaterialReservation
        from production.models import ProductionOrder, ProductionProcess
        
        # สร้าง group สำหรับ warehouse นี้
        group_name = f"warehouse_{self.id}_staff"
        group, created = Group.objects.get_or_create(name=group_name)

        # กำหนด permissions ที่ต้องสร้างสำหรับ warehouse นี้
        permissions_to_create = [
            # Warehouse Management
            {
                'model': Warehouse,
                'codename': f"can_manage_warehouse_{self.id}",
                'name': f"Can manage Warehouse {self.name} (ID {self.id})"
            },
            # Inventory Permissions
            {
                'model': Stock,
                'codename': f"can_view_stock_warehouse_{self.id}",
                'name': f"Can view stock in Warehouse {self.name}"
            },
            {
                'model': StockMovement,
                'codename': f"can_create_stock_movement_warehouse_{self.id}",
                'name': f"Can create stock movements in Warehouse {self.name}"
            },
            {
                'model': StockMovement,
                'codename': f"can_manage_stock_movement_warehouse_{self.id}",
                'name': f"Can manage stock movements in Warehouse {self.name}"
            },
            {
                'model': MaterialReservation,
                'codename': f"can_manage_reservation_warehouse_{self.id}",
                'name': f"Can manage material reservations in Warehouse {self.name}"
            },
            # Production Permissions
            {
                'model': ProductionOrder,
                'codename': f"can_create_production_order_warehouse_{self.id}",
                'name': f"Can create production orders in Warehouse {self.name}"
            },
            {
                'model': ProductionOrder,
                'codename': f"can_manage_production_order_warehouse_{self.id}",
                'name': f"Can manage production orders in Warehouse {self.name}"
            },
            {
                'model': ProductionProcess,
                'codename': f"can_manage_production_process_warehouse_{self.id}",
                'name': f"Can manage production processes in Warehouse {self.name}"
            },
        ]

        created_permissions = []
        for perm_config in permissions_to_create:
            content_type = ContentType.objects.get_for_model(perm_config['model'])
            permission, perm_created = Permission.objects.get_or_create(
                codename=perm_config['codename'],
                content_type=content_type,
                defaults={'name': perm_config['name']}
            )
            created_permissions.append(permission)
            
            # เพิ่ม permission ให้ group
            group.permissions.add(permission)

        # เพิ่ม permission ให้ superuser group ด้วย
        superuser_group, _ = Group.objects.get_or_create(name='superuser')
        for permission in created_permissions:
            superuser_group.permissions.add(permission)
        
        # เพิ่ม warehouse creator เข้า warehouse group โดยอัตโนมัติ
        if self.created_by:
            group.user_set.add(self.created_by)
            
        return group, created_permissions

    def get_warehouse_group(self):
        """Get the group associated with this warehouse"""
        group_name = f"warehouse_{self.id}_staff"
        try:
            return Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            return None

    def has_user_access(self, user, operation=None):
        """
        Check if user has access to this warehouse for specific operation
        
        Args:
            user: User instance to check
            operation: Optional operation type ('view_stock', 'manage_stock_movement', 
                      'manage_production', etc.)
        
        Returns:
            bool: True if user has access
        """
        if user.is_superuser:
            return True
            
        # Check if user is in warehouse group
        warehouse_group = self.get_warehouse_group()
        if warehouse_group and user.groups.filter(id=warehouse_group.id).exists():
            if operation is None:
                return True
            
            # Check specific operation permissions
            permission_codenames = {
                'view_stock': ('inventory', f"can_view_stock_warehouse_{self.id}"),
                'manage_stock_movement': ('inventory', f"can_manage_stock_movement_warehouse_{self.id}"),
                'create_stock_movement': ('inventory', f"can_create_stock_movement_warehouse_{self.id}"),
                'manage_reservation': ('inventory', f"can_manage_reservation_warehouse_{self.id}"),
                'create_production_order': ('production', f"can_create_production_order_warehouse_{self.id}"),
                'manage_production_order': ('production', f"can_manage_production_order_warehouse_{self.id}"),
                'view_production_process': ('production', f"can_manage_production_process_warehouse_{self.id}"),  # Use same permission for view
                'manage_production_process': ('production', f"can_manage_production_process_warehouse_{self.id}"),
                'manage_warehouse': ('inventory', f"can_manage_warehouse_{self.id}"),
            }
            
            if operation in permission_codenames:
                app_label, codename = permission_codenames[operation]
                return user.has_perm(f"{app_label}.{codename}")
                
        return False

    @classmethod
    def get_user_warehouses(cls, user, operation=None):
        """
        Get all warehouses that user has access to
        
        Args:
            user: User instance
            operation: Optional operation type to filter by
            
        Returns:
            QuerySet: Warehouses user can access
        """
        if user.is_superuser:
            return cls.objects.filter(is_active=True)
        
        # Get user's warehouse groups
        user_groups = user.groups.filter(name__startswith='warehouse_').values_list('name', flat=True)
        warehouse_ids = []
        
        for group_name in user_groups:
            # Extract warehouse ID from group name (format: warehouse_{id}_staff)
            parts = group_name.split('_')
            if len(parts) >= 2 and parts[0] == 'warehouse':
                try:
                    warehouse_id = int(parts[1])
                    warehouse_ids.append(warehouse_id)
                except ValueError:
                    continue
        
        # Filter by specific operation if provided
        warehouses = cls.objects.filter(id__in=warehouse_ids, is_active=True)
        
        if operation:
            # Further filter by checking specific permissions
            accessible_warehouses = []
            for warehouse in warehouses:
                if warehouse.has_user_access(user, operation):
                    accessible_warehouses.append(warehouse.id)
            warehouses = warehouses.filter(id__in=accessible_warehouses)
            
        return warehouses

    def assign_user(self, user):
        """
        Assign user to this warehouse by adding them to warehouse group
        
        Args:
            user: User instance to assign
            
        Returns:
            bool: True if successfully assigned
        """
        warehouse_group = self.get_warehouse_group()
        if not warehouse_group:
            # Create permissions if they don't exist
            warehouse_group, _ = self._create_warehouse_permissions()
            
        user.groups.add(warehouse_group)
        return True

    def remove_user(self, user):
        """
        Remove user from this warehouse by removing them from warehouse group
        
        Args:
            user: User instance to remove
            
        Returns:
            bool: True if successfully removed
        """
        warehouse_group = self.get_warehouse_group()
        if warehouse_group:
            user.groups.remove(warehouse_group)
            return True
        return False

    def get_assigned_users(self):
        """
        Get all users assigned to this warehouse
        
        Returns:
            QuerySet: Users in warehouse group
        """
        warehouse_group = self.get_warehouse_group()
        if warehouse_group:
            return warehouse_group.user_set.all()
        return User.objects.none()

    def delete(self, *args, **kwargs):
        """Override delete to clean up associated permissions and groups"""
        if self.id:
            # Remove associated group and permissions
            group_name = f"warehouse_{self.id}_staff"
            try:
                group = Group.objects.get(name=group_name)
                
                # Remove warehouse-specific permissions
                warehouse_permissions = Permission.objects.filter(
                    codename__endswith=f"_warehouse_{self.id}"
                )
                
                # Remove from superuser group as well
                try:
                    superuser_group = Group.objects.get(name='superuser')
                    superuser_group.permissions.remove(*warehouse_permissions)
                except Group.DoesNotExist:
                    pass
                
                # Delete permissions
                warehouse_permissions.delete()
                
                # Delete group
                group.delete()
                
            except Group.DoesNotExist:
                pass
        
        super().delete(*args, **kwargs)

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
