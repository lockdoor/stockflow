"""
Example views showing warehouse permission usage
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.http import JsonResponse

from inventory.models import Warehouse, Stock, StockMovement
from inventory.utils.warehouse_permissions import (
    WarehousePermissionMixin,
    require_warehouse_permission,
    check_warehouse_permission,
    get_user_warehouse_queryset
)


# Example function-based view with decorator
@login_required
@require_warehouse_permission('view_stock')
def warehouse_stock_view(request, warehouse_id):
    """View stock in a specific warehouse"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    stocks = Stock.objects.filter(warehouse=warehouse, available_quantity__gt=0)
    
    return render(request, 'inventory/warehouse_stock.html', {
        'warehouse': warehouse,
        'stocks': stocks
    })


# Example API view with permission checking
@login_required
def warehouse_stock_api(request, warehouse_id):
    """API endpoint for warehouse stock data"""
    # Manual permission check
    if not check_warehouse_permission(request.user, warehouse_id, 'view_stock', raise_exception=False):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    stocks = Stock.objects.filter(warehouse=warehouse, available_quantity__gt=0)
    
    stock_data = [{
        'item_name': stock.item_sku.name,
        'quantity': float(stock.available_quantity),
        'lot_number': stock.lot_number,
    } for stock in stocks]
    
    return JsonResponse({'stocks': stock_data})


# Example class-based view with mixin
class WarehouseStockListView(LoginRequiredMixin, WarehousePermissionMixin, ListView):
    """List stocks in user's accessible warehouses"""
    model = Stock
    template_name = 'inventory/stock_list.html'
    context_object_name = 'stocks'
    required_warehouse_operation = 'view_stock'
    
    def get_queryset(self):
        # The mixin automatically filters by user's warehouse access
        return super().get_queryset().filter(available_quantity__gt=0)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user's accessible warehouses to context
        context['accessible_warehouses'] = get_user_warehouse_queryset(
            self.request.user, 
            'view_stock'
        )
        return context


class StockMovementCreateView(LoginRequiredMixin, WarehousePermissionMixin, CreateView):
    """Create stock movement with warehouse permission checking"""
    model = StockMovement
    fields = ['reference_type', 'reference_id', 'note']
    required_warehouse_operation = 'create_stock_movement'
    
    def form_valid(self, form):
        # Set warehouse from URL
        warehouse_id = self.kwargs.get('warehouse_id')
        form.instance.warehouse_id = warehouse_id
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


# Example dashboard view showing user's warehouses
@login_required
def user_dashboard(request):
    """Dashboard showing user's accessible warehouses and stats"""
    accessible_warehouses = get_user_warehouse_queryset(request.user)
    
    warehouse_stats = []
    for warehouse in accessible_warehouses:
        # Check what operations user can perform
        operations = {}
        operations['can_view_stock'] = warehouse.has_user_access(request.user, 'view_stock')
        operations['can_create_movement'] = warehouse.has_user_access(request.user, 'create_stock_movement')
        operations['can_manage_production'] = warehouse.has_user_access(request.user, 'manage_production_order')
        
        # Get some basic stats
        stock_count = Stock.objects.filter(warehouse=warehouse, available_quantity__gt=0).count()
        movement_count = StockMovement.objects.filter(warehouse=warehouse, status='DRAFT').count()
        
        warehouse_stats.append({
            'warehouse': warehouse,
            'operations': operations,
            'stock_items': stock_count,
            'pending_movements': movement_count,
        })
    
    return render(request, 'dashboard/user_dashboard.html', {
        'warehouse_stats': warehouse_stats,
        'total_warehouses': accessible_warehouses.count(),
    })
