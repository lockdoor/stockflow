from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class WarehousePermissionMixin(UserPassesTestMixin):
    """
    Mixin to check warehouse-specific permissions
    
    Inherits from UserPassesTestMixin to leverage Django's built-in
    permission handling with custom warehouse-specific logic.
    """
    permission_required_base = None  # Should be set in child classes
    
    def test_func(self):
        """
        Test function for UserPassesTestMixin
        Check if user has either base permission or warehouse-specific permission
        """
        if not self.request.user.is_authenticated:
            return False
        
        warehouse_id = self.get_warehouse_id()
        if not warehouse_id:
            # If no warehouse_id, check only base permission
            return self.check_base_permission()
        
        return self.check_warehouse_permission(warehouse_id, self.get_permission_required_base())
    
    def get_permission_required_base(self):
        """Get the base permission required for this view"""
        if self.permission_required_base is None:
            raise NotImplementedError(
                f'{self.__class__.__name__} must define permission_required_base '
                'or override get_permission_required_base()'
            )
        return self.permission_required_base
    
    def check_base_permission(self):
        """Check if user has base permission (without warehouse-specific check)"""
        permission = f'inventory.{self.get_permission_required_base()}'
        return self.request.user.has_perm(permission)

    def check_warehouse_permission(self, warehouse_id, base_permission):
        """Check if user has either base permission or warehouse-specific permission"""
        if not self.request.user.is_authenticated:
            return False
            
        # Check base permission first
        base_perm = f'inventory.{base_permission}'
        if self.request.user.has_perm(base_perm):
            return True
        
        # Check warehouse-specific permission
        warehouse_perm = f'inventory.can_manage_warehouse_{warehouse_id}'
        return self.request.user.has_perm(warehouse_perm)
    
    def get_warehouse_id(self):
        """Get warehouse ID from URL kwargs or from object"""
        # First try to get from URL kwargs (for create/list views)
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id:
            return warehouse_id
            
        # Check for stock_movement_id and get warehouse from stock movement
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if stock_movement_id:
            try:
                from inventory.models.stock_movement import StockMovement
                stock_movement = StockMovement.objects.get(id=stock_movement_id)
                return stock_movement.warehouse.id
            except StockMovement.DoesNotExist:
                return None
            except Exception:
                return None
            
        # For update views, get from the object
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
                if hasattr(obj, 'warehouse'):
                    return obj.warehouse.id
                elif hasattr(obj, 'warehouse_id'):
                    return obj.warehouse_id
                elif hasattr(obj, 'stock_movement') and hasattr(obj.stock_movement, 'warehouse'):
                    return obj.stock_movement.warehouse.id
            except:
                # If get_object fails, return None
                pass
        
        # Try to get from form data for create views
        if hasattr(self, 'request') and self.request.method == 'POST':
            warehouse_id = self.request.POST.get('warehouse')
            if warehouse_id:
                return int(warehouse_id)
        
        return None
    
    def handle_no_permission(self):
        """
        Handle the case when user doesn't have permission
        Provides more specific error messages
        """
        warehouse_id = self.get_warehouse_id()
        if warehouse_id:
            raise PermissionDenied(
                f"You don't have permission to access warehouse {warehouse_id}. "
                f"Required permission: {self.get_permission_required_base()}"
            )
        else:
            raise PermissionDenied(
                f"You don't have permission to perform this action. "
                f"Required permission: {self.get_permission_required_base()}"
            )