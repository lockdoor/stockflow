from django.views.generic import CreateView, ListView, View, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy

# models
from inventory.models.stock_movement import StockMovement, StockMovementStatus
# forms
from inventory.forms.stock_movement_form import StockMovementForm

class StockMovementCreateView(LoginRequiredMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock/partials/stock-movement-form.html'
    
    def dispatch(self, request, *args, **kwargs):
        warehouse_id = self.kwargs.get('warehouse_id')
        perm1 = 'inventory.add_stockmovement'
        perm2 = f'inventory.can_manage_warehouse_{warehouse_id}'
        if not (request.user.has_perm(perm1) or request.user.has_perm(perm2)):
            return HttpResponse(status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super().get_initial()
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id:
            initial['warehouse'] = warehouse_id
        initial['status'] = StockMovementStatus.DRAFT
        return initial

    def form_valid(self, form):
        stock_movement = form.save(commit=False)
        stock_movement.created_by = self.request.user
        stock_movement.updated_by = self.request.user
        stock_movement.save()
        context = {'movement': stock_movement}
        response = render(self.request, 'inventory/stock/partials/stock-movement-row.html', context)
        response['HX-Trigger'] = 'success'
        return response

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#stock-movement-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class StockMovementByWareHouseListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/stock/partials/stock-movement-list.html'
    context_object_name = 'stock_movements'
    paginate_by = 20

    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        return StockMovement.objects.filter(warehouse_id=warehouse_id).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouse'] = self.kwargs.get('warehouse_id')
        return context
    
class StockMovementUpdateView(LoginRequiredMixin, UpdateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock/stock-movement-form.html'
    
    def dispatch(self, request, *args, **kwargs):
        stock_movement = self.get_object()
        warehouse_id = stock_movement.warehouse_id
        perm1 = 'inventory.change_stockmovement'
        perm2 = f'inventory.can_manage_warehouse_{warehouse_id}'
        if not (request.user.has_perm(perm1) or request.user.has_perm(perm2)):
            return HttpResponse(status=403)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        stock_movement = form.save(commit=False)
        stock_movement.updated_by = self.request.user
        stock_movement.save()
        context = {'stock_movement': stock_movement}
        response = render(self.request, 'inventory/stock/partials/stock-movement-row.html', context)
        response['HX-Trigger'] = 'success'
        return response

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#stock-movement-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class StockMovementDeleteView(LoginRequiredMixin, View):

    def delete(self, request, pk):
        try:
            stock_movement = StockMovement.objects.get(pk=pk)
            # Check if user has permission to manage the warehouse 
            perm = f'inventory.can_manage_warehouse_{stock_movement.warehouse_id}'
            if not request.user.has_perm(perm):
                return HttpResponse(status=403)
            if stock_movement.status == StockMovementStatus.CONFIRMED:
                return HttpResponse("Cannot delete confirmed movement.", status=400)
            stock_movement.delete()
            return HttpResponse(status=200)
        except StockMovement.DoesNotExist:
            return HttpResponse(status=404)
