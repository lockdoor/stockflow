from django.views.generic import CreateView, ListView, View, UpdateView, DetailView
from ..mixins.warehouse import WarehousePermissionMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, Http404, redirect, reverse
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied, ValidationError

# models
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
# forms
from inventory.forms.stock_movement_form import StockMovementForm

class StockMovementCreateView(LoginRequiredMixin, WarehousePermissionMixin,CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/partials/stock-movement-form.html'
    permission_required_base = 'add_stockmovement'
    
    def get(self, request, *args, **kwargs):
        # Check permissions for GET request
        warehouse_id = self.get_warehouse_id()
        if warehouse_id and not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
            raise PermissionDenied("You don't have permission to access this warehouse.")
        return super().get(request, *args, **kwargs)
    
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
        if warehouse_id and not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
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
    
class StockMovementUpdateView(LoginRequiredMixin, WarehousePermissionMixin, UpdateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/partials/stock-movement-form.html'
    permission_required_base = 'change_stockmovement'

    def get(self, request, *args, **kwargs):
        # Check permissions for GET request
        warehouse_id = self.get_warehouse_id()
        if warehouse_id and not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
            raise PermissionDenied("You don't have permission to access this warehouse.")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # Check permissions before saving
        warehouse_id = self.get_warehouse_id()
        if warehouse_id and not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
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
    
class StockMovementDeleteView(LoginRequiredMixin, WarehousePermissionMixin, View):
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
            if not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
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

class StockMovementConfirmView(LoginRequiredMixin, WarehousePermissionMixin, View):
    
    permission_required_base = 'change_stockmovement'
    http_method_names = ['post']

    def post(self, request, pk):
        # Debug breakpoint - uncomment when needed
        # import pdb; pdb.set_trace()
        
        try:
            stock_movement = get_object_or_404(StockMovement, pk=pk)
            
            # Check warehouse permissions before confirmation
            warehouse_id = stock_movement.warehouse.id
            if not self.check_warehouse_permission(warehouse_id, self.permission_required_base):
                raise PermissionDenied("You don't have permission to confirm stock movements in this warehouse.")
            
            # Check if already completed
            if stock_movement.status == StockMovement.Status.COMPLETED:
                return HttpResponse("Stock movement is already completed.", status=400)
            
            # Use the model's confirm method which handles immutability correctly
            stock_movement.confirm(request.user)
            
            # For HTMX requests, use HX-Redirect header
            if request.headers.get('HX-Request'):
                detail_url = reverse('inventory:stock-movement-detail', kwargs={'pk': stock_movement.pk})
                response = HttpResponse()
                response['HX-Redirect'] = detail_url
                return response
            else:
                # For regular requests, use normal redirect
                return redirect(reverse('inventory:stock-movement-detail', kwargs={'pk': stock_movement.pk}))
            
        except PermissionDenied as e:
            return HttpResponse(str(e), status=403)
        except ValidationError as e:
            return HttpResponse(f"Validation error: {str(e)}", status=400)
        except Http404:
            # Re-raise Http404 to let Django handle it properly
            raise
        except Exception as e:
            return HttpResponse(f"Error confirming stock movement: {str(e)}", status=500)
        