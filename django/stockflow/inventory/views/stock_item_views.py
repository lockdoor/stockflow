from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from ..mixins.warehouse import WarehousePermissionMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.stock_movement import StockMovement
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

# forms
from ..forms.stock_movement_item_form import StockMovementItemForm

class StockItemMovementListView(LoginRequiredMixin, ListView):
    model = StockMovementItem
    template_name = 'inventory/item-movement/partials/item-movement-list.html'
    context_object_name = 'movement_items'
    paginate_by = 20

    def get_queryset(self):
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if not stock_movement_id:
            raise Http404
        self.stock_movement = StockMovement.objects.filter(id=stock_movement_id).first()
        if not self.stock_movement:
            raise Http404("Stock movement not found")
        return StockMovementItem.objects.filter(stock_movement_id=stock_movement_id).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_movement'] = self.stock_movement
        return context

class StockItemMovementCreateView(LoginRequiredMixin, WarehousePermissionMixin,CreateView):
    model = StockMovementItem
    form_class = StockMovementItemForm
    template_name = 'inventory/item-movement/partials/item-movement-form.html'
    permission_required_base = 'add_stockmovementitem'
    
    def _check_permissions(self):
        """Check if user has permission to create stock movement items"""
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if not stock_movement_id:
            raise Http404("Stock movement ID is required")
        stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
        
        # Check if movement is confirmed (immutable)
        if stock_movement.status == StockMovement.Status.CONFIRMED:
            raise PermissionDenied("Cannot add items to confirmed stock movements.")
        
        warehouse_id = stock_movement.warehouse_id
        if not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
            raise PermissionDenied("You don't have permission to access this warehouse.")
    
    def get(self, request, *args, **kwargs):
        self._check_permissions()
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self._check_permissions()
        return super().post(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Add stock_movement_id to form kwargs"""
        kwargs = super().get_form_kwargs()
        kwargs['stock_movement_id'] = self.kwargs.get('stock_movement_id')
        return kwargs
    
    def get_initial(self):
        """Set initial data for the form"""
        initial = super().get_initial()
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if stock_movement_id:
            initial['stock_movement'] = stock_movement_id
        return initial
    
    def get_context_data(self, **kwargs):
        """Add warehouse to context"""
        context = super().get_context_data(**kwargs)
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if stock_movement_id:
            try:
                stock_movement = StockMovement.objects.get(id=stock_movement_id)
                context['warehouse'] = stock_movement.warehouse
                context['stock_movement'] = stock_movement
            except StockMovement.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        try:
            movement_item = form.save(commit=False)
            movement_item.created_by = self.request.user
            movement_item.updated_by = self.request.user
            movement_item.save()
            context = {'movement_item': movement_item}
            response = render(self.request, 'inventory/item-movement/partials/item-movement-row.html', context)
            response['HX-Trigger'] = 'success'
            return response
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        # Get stock movement for template context
        stock_movement_id = self.kwargs.get('stock_movement_id')
        stock_movement = None
        warehouse = None
        if stock_movement_id:
            try:
                stock_movement = StockMovement.objects.get(id=stock_movement_id)
                warehouse = stock_movement.warehouse
            except StockMovement.DoesNotExist:
                pass
        
        context = {
            'form': form,
            'stock_movement': stock_movement,
            'warehouse': warehouse
        }
        response = render(self.request, self.template_name, context)
        response['HX-Retarget'] = '#item-movement-form'
        response['HX-Reswap'] = 'innerHTML'
        return response