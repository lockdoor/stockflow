class WarehousePermissionMixin:
    """Mixin to check warehouse-specific permissions"""

    def check_warehouse_permission(self, warehouse_id, base_permission):
        """Check if user has either base permission or warehouse-specific permission"""
        if not self.request.user.is_authenticated:
            return False
            
        perm1 = f'inventory.{base_permission}'
        perm2 = f'inventory.can_manage_warehouse_{warehouse_id}'
        return self.request.user.has_perm(perm1) or self.request.user.has_perm(perm2)
    
    def get_warehouse_id(self):
        """Get warehouse ID from URL kwargs or from object"""
        # First try to get from URL kwargs (for create/list views)
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id:
            return warehouse_id
            
        # For update views, get from the object
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, 'warehouse'):
                return obj.warehouse.id
        
        return None