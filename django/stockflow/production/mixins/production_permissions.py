"""
Production Permissions Mixin

Mixin สำหรับจัดการ permissions ใน production views
Based on WarehousePermissionMixin pattern for consistency
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy


class ProductionPermissionMixin(UserPassesTestMixin):
    """
    Production permission mixin with warehouse context support
    
    Inherits from UserPassesTestMixin to leverage Django's built-in
    permission handling with production and warehouse-specific logic.
    """
    permission_required_base = None  # Should be set in child classes
    login_url = reverse_lazy('login')  # Redirect anonymous users to login page
    
    def test_func(self):
        """
        Test function for UserPassesTestMixin
        Check if user has either production permission or warehouse-specific permission
        """
        if not self.request.user.is_authenticated:
            return False
        
        warehouse_id = self.get_warehouse_id()
        if not warehouse_id:
            # If no warehouse_id, check only base production permission
            return self.check_base_permission()
        
        return self.check_warehouse_production_permission(warehouse_id, self.get_permission_required_base())
    
    def handle_no_permission(self):
        """
        Override to ensure anonymous users are redirected to login page
        """
        if not self.request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        
        # For authenticated users without permission, raise PermissionDenied
        raise PermissionDenied("You don't have permission to access this resource")
    
    def get_permission_required_base(self):
        """Get the base permission required for this view"""
        if self.permission_required_base is None:
            raise NotImplementedError(
                f'{self.__class__.__name__} must define permission_required_base '
                'or override get_permission_required_base()'
            )
        return self.permission_required_base
    
    def check_base_permission(self):
        """Check if user has base production permission"""
        permission = f'production.{self.get_permission_required_base()}'
        return self.request.user.has_perm(permission)

    def check_warehouse_production_permission(self, warehouse_id, base_permission):
        """
        Check if user has either base production permission or warehouse-specific permission
        Production permissions follow this hierarchy:
        1. Global production permission (production.{action})
        2. Warehouse-specific permission (inventory.can_manage_warehouse_{id})
        3. Admin permissions (superuser)
        """
        if not self.request.user.is_authenticated:
            return False
            
        # Superusers have access to everything
        if self.request.user.is_superuser:
            return True
            
        # Check base production permission first
        base_perm = f'production.{base_permission}'
        if self.request.user.has_perm(base_perm):
            return True
        
        # Check warehouse-specific permission
        # Production operations require warehouse management access
        warehouse_perm = f'inventory.can_manage_warehouse_{warehouse_id}'
        return self.request.user.has_perm(warehouse_perm)
    
    def get_warehouse_id(self):
        """
        Get warehouse ID from production order context
        Production operations are always tied to a warehouse through production order
        """
        # First try to get from URL kwargs
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id:
            return warehouse_id
            
        # Try to get production_order_id and get warehouse from it
        production_order_id = self.kwargs.get('production_order_id') or self.kwargs.get('pk')
        if production_order_id:
            try:
                from production.models import ProductionOrder
                production_order = ProductionOrder.objects.get(id=production_order_id)
                return production_order.warehouse.id
            except ProductionOrder.DoesNotExist:
                return None
            except Exception:
                return None
            
        # For update/detail views, get from the object
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
                # ProductionProcess → ProductionOrder → Warehouse
                if hasattr(obj, 'production_order') and hasattr(obj.production_order, 'warehouse'):
                    return obj.production_order.warehouse.id
                # ProductionOrder → Warehouse  
                elif hasattr(obj, 'warehouse'):
                    return obj.warehouse.id
                elif hasattr(obj, 'warehouse_id'):
                    return obj.warehouse_id
            except:
                # If get_object fails, return None
                pass
        
        # Try to get from form data for create views
        if hasattr(self, 'request') and self.request.method == 'POST':
            warehouse_id = self.request.POST.get('warehouse')
            if warehouse_id:
                try:
                    return int(warehouse_id)
                except (ValueError, TypeError):
                    pass
        
        return None
    
    def handle_no_permission(self):
        """
        Handle the case when user doesn't have permission
        Provides more specific error messages for production context
        """
        warehouse_id = self.get_warehouse_id()
        if warehouse_id:
            raise PermissionDenied(
                f"You don't have permission to access production operations for warehouse {warehouse_id}. "
                f"Required permission: {self.get_permission_required_base()} or warehouse management access."
            )
        else:
            raise PermissionDenied(
                f"You don't have permission to perform this production operation. "
                f"Required permission: {self.get_permission_required_base()}"
            )
