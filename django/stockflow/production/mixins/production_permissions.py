"""
Production Permissions Mixin

Mixin สำหรับจัดการ permissions ใน production views
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class ProductionPermissionMixin(LoginRequiredMixin):
    """
    Base permission mixin for production views
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Add additional permission checks here if needed
        # For now, just require login
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_production_permission(self, user):
        """
        Override this method in subclasses to add specific permission logic
        """
        return user.is_authenticated
    
    def check_production_permissions(self):
        """
        Check production-specific permissions
        """
        if not self.has_production_permission(self.request.user):
            raise PermissionDenied("You don't have permission to access production features.")
