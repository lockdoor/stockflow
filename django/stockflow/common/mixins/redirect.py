"""
Redirect Mixins for handling complex redirect logic in views.

This module provides mixins for consistent redirect behavior across views,
particularly for handling 'next' and 'prev' parameters.
"""

from django.shortcuts import reverse
from django.http import HttpResponseRedirect


class RedirectMixin:
    """
    Mixin for handling complex redirect logic with next/prev parameters.
    Provides consistent redirect behavior across CRUD views.
    """
    
    def get_success_redirect_url(self, obj=None):
        """
        Determine where to redirect after successful operation.
        Priority:
        1. 'next' parameter from request (POST takes priority over GET)
        2. Default success URL based on view type
        
        Args:
            obj: The model instance (optional, for object-specific redirects)
        
        Returns:
            str: URL to redirect to
        """
        # Check for next parameter in request (POST has priority)
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
            
        # Get default success URL
        return self.get_default_success_url(obj)
    
    def get_prev_redirect_url(self, obj=None):
        """
        Determine where to redirect when user cancels or on error.
        Priority:
        1. 'prev' parameter from request
        2. Default previous URL based on view type
        
        Args:
            obj: The model instance (optional, for object-specific redirects)
        
        Returns:
            str: URL to redirect to
        """
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev') or self.request.POST.get('prev')
        if prev_url:
            return prev_url
            
        # Get default previous URL
        return self.get_default_prev_url(obj)
    
    def get_default_success_url(self, obj=None):
        """
        Get the default success URL when no 'next' parameter is provided.
        Subclasses should override this method.
        
        Args:
            obj: The model instance
        
        Returns:
            str: Default success URL
        """
        if hasattr(self, 'success_url') and self.success_url:
            return self.success_url
            
        if obj and hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
            
        # Fallback to model list view
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        try:
            return reverse(f'{app_label}:{model_name}-list')
        except:
            return '/'
    
    def get_default_prev_url(self, obj=None):
        """
        Get the default previous URL when no 'prev' parameter is provided.
        Different behavior for Create vs Update/Delete views.
        
        Args:
            obj: The model instance
        
        Returns:
            str: Default previous URL
        """
        # For update/delete views, prefer detail page
        if obj and hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
            
        # For create views or fallback, go to list
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        try:
            return reverse(f'{app_label}:{model_name}-list')
        except:
            return '/'
    
    def redirect_success(self, obj=None):
        """
        Helper method to redirect to success URL.
        
        Args:
            obj: The model instance
        
        Returns:
            HttpResponseRedirect: Redirect response
        """
        url = self.get_success_redirect_url(obj)
        return HttpResponseRedirect(url)
    
    def redirect_prev(self, obj=None):
        """
        Helper method to redirect to previous URL.
        
        Args:
            obj: The model instance
        
        Returns:
            HttpResponseRedirect: Redirect response
        """
        url = self.get_prev_redirect_url(obj)
        return HttpResponseRedirect(url)


class StockMovementRedirectMixin(RedirectMixin):
    """
    Specialized redirect mixin for StockMovement views.
    Provides StockMovement-specific default URLs.
    """
    
    def get_default_success_url(self, stock_movement=None):
        """Get default success URL for stock movement operations."""
        if stock_movement:
            return reverse('inventory:stock-movement-detail', kwargs={'pk': stock_movement.pk})
        return reverse('inventory:stock-movement-list')
    
    def get_default_prev_url(self, stock_movement=None):
        """Get default previous URL for stock movement operations."""
        if stock_movement:
            # For update operations, prefer detail page
            if hasattr(self, 'object') and self.object:
                return reverse('inventory:stock-movement-detail', kwargs={'pk': stock_movement.pk})
        return reverse('inventory:stock-movement-list')
