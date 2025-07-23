from django.views.generic import CreateView, ListView, View, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, Http404
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

# models
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
# forms
from inventory.forms.stock_movement_form import StockMovementForm


class WarehousePermissionMixin:
    """Mixin to check warehouse-specific permissions"""
    
    def _check_warehouse_permission(self, warehouse_id, base_permission):
        """Check if user has either base permission or warehouse-specific permission"""
        if not self.request.user.is_authenticated:
            return False
            
        perm1 = f'inventory.{base_permission}'
        perm2 = f'inventory.can_manage_warehouse_{warehouse_id}'
        return self.request.user.has_perm(perm1) or self.request.user.has_perm(perm2)
    
    def _get_warehouse_id(self):
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
    
    def dispatch(self, request, *args, **kwargs):
        # Let parent handle authentication first (LoginRequiredMixin)
        response = super().dispatch(request, *args, **kwargs)
        
        # If response is a redirect (like login redirect), return it
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
            
        # Check warehouse permissions
        warehouse_id = self._get_warehouse_id()
        if warehouse_id and hasattr(self, 'permission_required_base'):
            if not self._check_warehouse_permission(warehouse_id, self.permission_required_base):
                raise PermissionDenied("You don't have permission to access this warehouse.")
                
        return response


class WarehousePermissionBaseMixin:
    """Base mixin with permission methods but no dispatch check"""
    
    def _check_warehouse_permission(self, warehouse_id, base_permission):
        """Check if user has either base permission or warehouse-specific permission"""
        if not self.request.user.is_authenticated:
            return False
            
        perm1 = f'inventory.{base_permission}'
        perm2 = f'inventory.can_manage_warehouse_{warehouse_id}'
        return self.request.user.has_perm(perm1) or self.request.user.has_perm(perm2)
    
    def _get_warehouse_id(self):
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


class StockMovementCreateView(LoginRequiredMixin, WarehousePermissionMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/partials/stock-movement-form.html'
    permission_required_base = 'add_stockmovement'
    
    def get_initial(self):
        initial = super().get_initial()
        warehouse_id = self.kwargs.get('warehouse_id')
        if not warehouse_id:
            raise Http404("Warehouse ID is required to create a stock movement.")
        initial['warehouse'] = warehouse_id  # Use ID for form field
        return initial

    def form_valid(self, form):
        # Check permissions before saving
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id and not self._check_warehouse_permission(warehouse_id, self.permission_required_base):
            raise PermissionDenied("You don't have permission to access this warehouse.")
            
        try:
            stock_movement = form.save(commit=False)
            stock_movement.created_by = self.request.user
            stock_movement.updated_by = self.request.user
            stock_movement.save()
            context = {'movement': stock_movement}  # Changed key to match template
            response = render(self.request, 'inventory/stock-movement/partials/stock-movement-row.html', context)
            response['HX-Trigger'] = 'success'
            return response
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Get warehouse for template context
        warehouse_id = self.kwargs.get('warehouse_id')
        warehouse = None
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                pass
        
        context = {
            'form': form,
            'warehouse': warehouse
        }
        response = render(self.request, self.template_name, context)
        response['HX-Retarget'] = '#stock-movement-form'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class StockMovementByWarehouseListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/stock-movement/partials/stock-movement-list.html'
    context_object_name = 'stock_movements'
    paginate_by = 20

    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        if not warehouse_id:
            raise Http404("Warehouse ID is required to list stock movements.")
        self.warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
        return StockMovement.objects.filter(warehouse_id=warehouse_id).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouse'] = self.warehouse
        return context
    
class StockMovementUpdateView(LoginRequiredMixin, WarehousePermissionBaseMixin, UpdateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/partials/stock-movement-form.html'
    permission_required_base = 'change_stockmovement'

    def get(self, request, *args, **kwargs):
        # Check permissions for GET request
        warehouse_id = self._get_warehouse_id()
        if warehouse_id and not self._check_warehouse_permission(warehouse_id, self.permission_required_base):
            raise PermissionDenied("You don't have permission to access this warehouse.")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # Check permissions before saving
        warehouse_id = self._get_warehouse_id()
        if warehouse_id and not self._check_warehouse_permission(warehouse_id, self.permission_required_base):
            raise PermissionDenied("You don't have permission to access this warehouse.")
            
        try:
            stock_movement = form.save(commit=False)
            stock_movement.updated_by = self.request.user
            stock_movement.save()
            context = {'stock_movement': stock_movement}  # Use stock_movement key for detail template
            response = render(self.request, 'inventory/stock-movement/partials/stock-movement-detail.html', context)
            response['HX-Trigger'] = 'success'
            return response
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#stock-movement-form'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class StockMovementDeleteView(LoginRequiredMixin, WarehousePermissionBaseMixin, View):
    permission_required_base = 'delete_stockmovement'

    def dispatch(self, request, *args, **kwargs):
        # Handle authentication first
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
        return response

    def delete(self, request, pk):
        try:
            stock_movement = get_object_or_404(StockMovement, pk=pk)
            
            # Check warehouse permissions before deletion
            warehouse_id = stock_movement.warehouse.id
            if not self._check_warehouse_permission(warehouse_id, self.permission_required_base):
                raise PermissionDenied("You don't have permission to delete stock movements in this warehouse.")
            
            # Check business rules
            if stock_movement.status == StockMovement.Status.CONFIRMED:
                return HttpResponse("Cannot delete confirmed movement.", status=400)
            
            stock_movement.delete()
            response = HttpResponse(status=200)
            response['HX-Trigger'] = 'stockMovementDeleted'
            return response
            
        except StockMovement.DoesNotExist:
            return HttpResponse(status=404)
        except PermissionDenied as e:
            return HttpResponse(str(e), status=403)

class StockMovementDetailView(LoginRequiredMixin, DetailView):
    model = StockMovement
    template_name = 'inventory/stock-movement/stock-movement-detail.html'
    context_object_name = 'stock_movement'
