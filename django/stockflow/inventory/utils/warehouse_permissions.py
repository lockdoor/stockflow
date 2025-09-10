"""
Warehouse permission utilities

Helper functions for checking warehouse-specific permissions
"""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from inventory.models import Warehouse


def check_warehouse_permission(user, warehouse_id, operation=None, raise_exception=True):
    """
    Check if user has permission for warehouse operation
    
    Args:
        user: User instance
        warehouse_id: Warehouse ID to check
        operation: Optional operation type
        raise_exception: Whether to raise PermissionDenied on failure
        
    Returns:
        bool: True if user has permission
        
    Raises:
        PermissionDenied: If user doesn't have permission and raise_exception=True
    """
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    has_permission = warehouse.has_user_access(user, operation)
    
    if not has_permission and raise_exception:
        operation_text = f" for {operation}" if operation else ""
        raise PermissionDenied(f"You don't have permission to access {warehouse}{operation_text}")
    
    return has_permission


def get_user_warehouse_queryset(user, operation=None):
    """
    Get warehouses that user can access
    
    Args:
        user: User instance
        operation: Optional operation filter
        
    Returns:
        QuerySet: Accessible warehouses
    """
    return Warehouse.get_user_warehouses(user, operation)


def filter_warehouse_queryset(queryset, user, operation=None):
    """
    Filter any queryset by user's warehouse access
    
    Args:
        queryset: QuerySet to filter
        user: User instance
        operation: Optional operation type
        
    Returns:
        QuerySet: Filtered queryset
    """
    accessible_warehouses = get_user_warehouse_queryset(user, operation)
    accessible_warehouse_ids = accessible_warehouses.values_list('id', flat=True)
    
    # Assume the model has a 'warehouse' field
    if hasattr(queryset.model, 'warehouse'):
        return queryset.filter(warehouse_id__in=accessible_warehouse_ids)
    
    # For models that might reference warehouse differently
    if hasattr(queryset.model, 'production_order'):
        return queryset.filter(production_order__warehouse_id__in=accessible_warehouse_ids)
        
    return queryset


class WarehousePermissionMixin:
    """
    Mixin for views that need warehouse permission checking
    """
    required_warehouse_operation = None
    warehouse_field = 'warehouse'
    
    def dispatch(self, request, *args, **kwargs):
        """Check warehouse permissions before processing request"""
        warehouse_id = self.get_warehouse_id()
        if warehouse_id:
            check_warehouse_permission(
                request.user, 
                warehouse_id, 
                self.required_warehouse_operation
            )
        return super().dispatch(request, *args, **kwargs)
    
    def get_warehouse_id(self):
        """Get warehouse ID from URL kwargs or object"""
        # Try custom method first
        if hasattr(self, 'get_warehouse_from_request'):
            warehouse = self.get_warehouse_from_request()
            return warehouse.id if warehouse else None
            
        # Try to get from URL kwargs
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id:
            return warehouse_id
            
        # Try to get from object
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, self.warehouse_field):
                warehouse = getattr(obj, self.warehouse_field)
                return warehouse.id if warehouse else None
                
        return None
    
    def get_queryset(self):
        """Filter queryset by user's warehouse access"""
        queryset = super().get_queryset()
        return filter_warehouse_queryset(
            queryset, 
            self.request.user, 
            self.required_warehouse_operation
        )


def require_warehouse_permission(operation=None):
    """
    Decorator for view functions that require warehouse permissions
    
    Args:
        operation: Required operation type
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            warehouse_id = kwargs.get('warehouse_id')
            if warehouse_id:
                check_warehouse_permission(request.user, warehouse_id, operation)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
