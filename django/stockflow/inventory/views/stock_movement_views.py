from django.views.generic import CreateView, ListView, View, UpdateView, DetailView
from ..mixins.warehouse import WarehousePermissionMixin
from common.mixins.redirect import StockMovementRedirectMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, Http404, redirect, reverse
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied, ValidationError

# models
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
# forms
from inventory.forms.stock_movement_form import StockMovementForm

class StockMovementListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/stock-movement/stock-movement-list.html'
    context_object_name = 'stock_movements'
    paginate_by = 20

    def get_queryset(self):
        return StockMovement.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # No specific warehouse context needed
        return context

class StockMovementCreateView(StockMovementRedirectMixin, WarehousePermissionMixin, LoginRequiredMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/stock-movement-form.html'
    permission_required_base = 'add_stockmovement'
    
    def get_initial(self):
        initial = super().get_initial()
        initial['reference_type'] = self.request.GET.get('reference_type')
        initial['reference_id'] = self.request.GET.get('reference_id')
        initial['warehouse'] = self.request.GET.get('warehouse')
        return initial
    
    def form_valid(self, form):
        try:
            stock_movement = form.save(commit=False)
            stock_movement.created_by = self.request.user
            stock_movement.updated_by = self.request.user
            stock_movement.save()
            
            # Use mixin's redirect method
            return self.redirect_success(stock_movement)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add next URL to context for template usage
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url()
        if self.request.GET.get('reference_type'):
            context['reference_type'] = self.request.GET.get('reference_type', '')
            context['reference_id'] = self.request.GET.get('reference_id', '')
        warehouse_id = self.request.GET.get('warehouse', '')
        if warehouse_id:
            warehouse = Warehouse.objects.get(pk=warehouse_id)
            context['warehouse'] = warehouse
        return context

class StockMovementUpdateView(StockMovementRedirectMixin, WarehousePermissionMixin, LoginRequiredMixin, UpdateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/stock-movement-form.html'
    permission_required_base = 'change_stockmovement'
    
    def get_initial(self):
        initial = super().get_initial()
        sm = self.get_object()
        initial['reference_type'] = sm.reference_type
        initial['reference_id'] = sm.reference_id
        initial['warehouse'] = sm.warehouse
        return initial

    def form_valid(self, form):            
        try:
            stock_movement = form.save(commit=False)
            stock_movement.updated_by = self.request.user
            stock_movement.save()
            
            # Use mixin's redirect method
            return self.redirect_success(stock_movement)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add next URL to context for template usage
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url(self.object)
        context['reference_type'] = self.object.reference_type
        context['reference_id'] = self.object.reference_id
        context['warehouse'] = self.object.warehouse
        return context

class StockMovementDetailView(LoginRequiredMixin, DetailView):
    model = StockMovement
    template_name = 'inventory/stock-movement/stock-movement-detail.html'
    context_object_name = 'stock_movement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add movement items to context
        context['movement_items'] = self.object.movement_items.select_related(
            'item_sku', 'item_sku__category'
        ).order_by('created_at')
        
        # Add primary image to context
        context['primary_image'] = self.object.images.filter(is_primary=True).first()
        context['images_count'] = self.object.images.count()
        
        if self.object.reference_type == self.__class__.model.ReferenceType.PRODUCTION:
            context['management_items_url'] = reverse(
                'inventory:movement-production-create',
                kwargs={'stock_movement_id': self.object.pk})
        else:
            context['management_items_url'] = reverse(
                'inventory:movement-create', 
                kwargs={'stock_movement_id': self.object.pk})
        return context

class StockMovementDeleteView(StockMovementRedirectMixin, WarehousePermissionMixin, LoginRequiredMixin, View):
    permission_required_base = 'delete_stockmovement'

    def delete(self, request, pk):
        """
        Handle DELETE request to remove a stock movement.
        Template should include 'next' parameter to specify redirect URL.
        If not provided, redirects to general stock movement list.
        """
        try:
            stock_movement = get_object_or_404(StockMovement, pk=pk)
            
            # Check business rules
            if stock_movement.status == StockMovement.Status.CONFIRMED:
                from django.contrib import messages
                messages.error(request, "Cannot delete confirmed movement.")
                return redirect('inventory:stock-movement-detail', pk=pk)
            
            # Get redirect URL before deletion (use mixin)
            success_url = self.get_success_redirect_url(stock_movement)
            
            # Delete the stock movement
            stock_movement.delete()
            
            from django.contrib import messages
            messages.success(request, "Stock movement deleted successfully.")
            return redirect(success_url)
            
        except StockMovement.DoesNotExist:
            raise Http404("Stock movement not found")
        except PermissionDenied as e:
            from django.contrib import messages
            messages.error(request, str(e))
            return redirect('inventory:stock-movement-detail', pk=pk)

    def post(self, request, pk):
        """Handle POST request by delegating to delete method."""
        return self.delete(request, pk)
   
class StockMovementConfirmView(StockMovementRedirectMixin, WarehousePermissionMixin, LoginRequiredMixin, View):
    permission_required_base = 'change_stockmovement'
    http_method_names = ['post']

    def post(self, request, pk):
        # Debug breakpoint - uncomment when needed
        # import pdb; pdb.set_trace()
        
        try:
            stock_movement = get_object_or_404(StockMovement, pk=pk)
            
            # Check if already completed
            if stock_movement.status == StockMovement.Status.COMPLETED:
                from django.contrib import messages
                messages.warning(request, "Stock movement is already completed.")
                return self.redirect_prev(stock_movement)
            
            # Use the model's confirm method which handles immutability correctly
            stock_movement.confirm(request.user)
            
            from django.contrib import messages
            messages.success(request, "Stock movement confirmed successfully.")
            return redirect('inventory:stock-movement-detail', pk=stock_movement.pk)
            
        except PermissionDenied as e:
            from django.contrib import messages
            messages.error(request, str(e))
            return self.redirect_prev(stock_movement)
        except ValidationError as e:
            from django.contrib import messages
            messages.error(request, f"Validation error: {str(e)}")
            return self.redirect_prev(stock_movement)
        except Http404:
            # Re-raise Http404 to let Django handle it properly
            raise
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f"Error confirming stock movement: {str(e)}")
            return self.redirect_prev(stock_movement)
