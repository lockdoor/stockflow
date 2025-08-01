from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from inventory.models import Stock
from django.http import HttpResponseBadRequest

class StockIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/stock/index.html'

class StockListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/stock/partials/stock-list.html'
    context_object_name = 'stock'
    paginate_by = 20
    
    def get_queryset(self): 
        return Stock.get_all_stock()
    
class StockItemListView(LoginRequiredMixin, ListView):
    """
    List all stock records by lot number for a specific item and warehouse.
    Shows individual lot records with quantities greater than zero by default.
    
    Query Parameters:
    - item_sku_id: Required. ID of the ItemSKU to filter by
    - warehouse_id: Required. ID of the Warehouse to filter by  
    - all: Optional. If 'true', shows all records including zero quantities
    """
    template_name = 'inventory/stock/stock-item-lot.html'
    context_object_name = 'stock_records'
    paginate_by = 20

    def get_queryset(self):
        """
        Get stock records filtered by item_sku and warehouse.
        Orders by expiry_date and lot_number for FEFO.
        """
        # Get and validate parameters
        item_sku_id = self.request.GET.get('item_sku_id')
        warehouse_id = self.request.GET.get('warehouse_id')
        show_all = self.request.GET.get('all', 'false').lower() == 'true'
        
        # Validate required parameters
        if not item_sku_id:
            return Stock.objects.none()
        
        if not warehouse_id:
            return Stock.objects.none()
        
        # Build base queryset
        queryset = Stock.objects.filter(
            item_sku_id=item_sku_id,
            warehouse_id=warehouse_id
        ).select_related('item_sku', 'warehouse')
        
        # Filter by quantity if not showing all
        if not show_all:
            queryset = queryset.filter(available_quantity__gt=0)
        
        # Order by expiry date for FEFO, then by lot number
        return queryset.order_by(
            models.F('expiry_date').asc(nulls_last=True), 
            'lot_number', 
            'created_at'
        )
    
    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        
        # Add filter parameters to context
        context['item_sku_id'] = self.request.GET.get('item_sku_id')
        context['warehouse_id'] = self.request.GET.get('warehouse_id')
        context['show_all'] = self.request.GET.get('all', 'false').lower() == 'true'
        
        # Add summary information
        if context['item_sku_id'] and context['warehouse_id']:
            try:
                from inventory.models.stock import Stock
                from catalog.models.item import ItemSKU
                from inventory.models.warehouse import Warehouse
                
                # Get total available stock
                total_stock = Stock.get_total_stock(
                    ItemSKU.objects.get(id=context['item_sku_id']),
                    Warehouse.objects.get(id=context['warehouse_id'])
                )
                context['total_available_stock'] = total_stock
                
                # Get item and warehouse info
                context['item_sku'] = ItemSKU.objects.get(id=context['item_sku_id'])
                context['warehouse'] = Warehouse.objects.get(id=context['warehouse_id'])
                
            except (ItemSKU.DoesNotExist, Warehouse.DoesNotExist):
                context['total_available_stock'] = 0
                context['error_message'] = "Item or Warehouse not found"
        
        return context
