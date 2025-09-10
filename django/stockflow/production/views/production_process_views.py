"""
Production Process Views

Views for managing individual production process operations like delete.
This is separate from the unified view for specific CRUD operations.
"""

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DeleteView
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from production.models.production_process import ProductionProcess
from production.models.production_order import ProductionOrder
from production.mixins.production_permissions import ProductionPermissionMixin
from common.mixins.redirect import RedirectMixin


class ProductionProcessDeleteView(ProductionPermissionMixin, RedirectMixin, DeleteView):
    """
    View for deleting production processes.
    Only allows deletion of DRAFT processes.
    """
    model = ProductionProcess
    template_name = 'production/production-process/production-process-confirm-delete.html'
    context_object_name = 'production_process'
    
    required_permission = 'production_process.delete'
    permission_denied_message = "You don't have permission to delete production processes."
    
    def get_object(self, queryset=None):
        """Get the production process and ensure it belongs to the correct production order"""
        production_order_id = self.kwargs['production_order_id']
        process_id = self.kwargs['process_id']
        
        # Get production order first
        production_order = get_object_or_404(ProductionOrder, pk=production_order_id)
        
        # Get production process and ensure it belongs to the production order
        production_process = get_object_or_404(
            ProductionProcess,
            pk=process_id,
            production_order=production_order
        )
        
        # Only allow deletion of DRAFT processes
        if production_process.status != 'DRAFT':
            raise PermissionDenied("Cannot delete confirmed production processes.")
        
        return production_process
    
    def get_context_data(self, **kwargs):
        """Add extra context for the template"""
        context = super().get_context_data(**kwargs)
        
        production_process = self.get_object()
        context['production_order'] = production_process.production_order
        
        # Add counts for related objects
        context['results_count'] = production_process.production_results.count()
        context['losses_count'] = production_process.production_losses.count()
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Handle the deletion"""
        self.object = self.get_object()
        production_order = self.object.production_order
        
        # Store process name for success message
        process_name = self.object.process_name
        
        # Perform the deletion
        success_url = self.get_success_url()
        self.object.delete()
        
        # Add success message
        messages.success(
            request,
            f'Production process "{process_name}" has been deleted successfully.'
        )
        
        return redirect(success_url)
    
    def get_success_url(self):
        """Redirect to production order detail after successful deletion"""
        return reverse('production:production-order-detail', args=[self.object.production_order.id])
    
    def get_default_success_url(self, obj=None):
        """Override RedirectMixin method"""
        if obj:
            return reverse('production:production-order-detail', args=[obj.production_order.id])
        return reverse('production:production-order-list')
    
    def get_default_prev_url(self, obj=None):
        """Override RedirectMixin method"""
        if obj:
            return reverse('production:production-order-detail', args=[obj.production_order.id])
        return reverse('production:production-order-list')
