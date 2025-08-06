"""
Stock Overview View

Shows stock balance for all items grouped by warehouse with optimized queries and frontend search.

Author: StockFlow Team
Created: 2025
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Case, When, IntegerField, Prefetch
from django.core.serializers import serialize
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from inventory.models import Stock, Warehouse
from catalog.models.item import ItemSKU


class StockOverviewView(LoginRequiredMixin, TemplateView):
    """
    Stock Overview View with Optimized Queries and Frontend Search
    
    Displays stock balances for all items grouped by warehouse.
    Uses single optimized query and frontend filtering for better performance.
    """
    template_name = 'inventory/stock/stock-overview.html'
    
    def get_context_data(self, **kwargs):
        """Add optimized stock overview data to context"""
        context = super().get_context_data(**kwargs)
        
        # Get all active warehouses
        warehouses = Warehouse.objects.filter(is_active=True).order_by('name')
        context['warehouses'] = warehouses
        
        # Get optimized stock data
        stock_data = self.get_optimized_stock_data()
        context['stock_overview'] = stock_data['items']
        context['stock_data_json'] = json.dumps(stock_data['json_data'])
        
        # Get summary statistics
        context.update(self.get_summary_statistics(stock_data['items']))
        
        return context
    
    def get_optimized_stock_data(self):
        """
        Get stock overview data with optimized single query.
        Returns both template data and JSON data for frontend search.
        """
        # Get all active warehouses for dynamic annotations
        warehouses = list(Warehouse.objects.filter(is_active=True).order_by('name'))
        
        # Build dynamic annotations for each warehouse
        warehouse_annotations = {}
        for warehouse in warehouses:
            warehouse_annotations[f'warehouse_{warehouse.id}_qty'] = Sum(
                Case(
                    When(stocks__warehouse=warehouse, then='stocks__available_quantity'),
                    default=0,
                    output_field=IntegerField()
                )
            )
        
        # Single optimized query with all data
        items_queryset = ItemSKU.objects.filter(
            stocks__available_quantity__gt=0,
            status=ItemSKU.Status.ACTIVE
        ).distinct().select_related('category').annotate(
            total_quantity=Sum('stocks__available_quantity'),
            **warehouse_annotations
        ).order_by('-total_quantity', 'sku_code')
        
        # Prepare data for template and JSON
        items_data = []
        json_data = []
        
        for item in items_queryset:
            # Prepare warehouse data
            warehouses_data = []
            for warehouse in warehouses:
                qty = getattr(item, f'warehouse_{warehouse.id}_qty', 0) or 0
                if qty > 0:
                    warehouses_data.append({
                        'warehouse__id': warehouse.id,
                        'warehouse__name': warehouse.name,
                        'warehouse__code': warehouse.code,
                        'total_quantity': qty
                    })
            
            # Template data structure (keeping compatibility)
            item_data = {
                'item': item,
                'warehouses': warehouses_data,
                'total_quantity': item.total_quantity or 0
            }
            items_data.append(item_data)
            
            # JSON data for frontend search
            json_item = {
                'id': item.id,
                'sku_code': item.sku_code,
                'name': item.name,
                'unit': item.unit,
                'type': item.type,
                'category': item.category.name if item.category else '',
                'total_quantity': float(item.total_quantity or 0),
                'warehouses': {}
            }
            
            # Add warehouse quantities to JSON
            for warehouse in warehouses:
                qty = getattr(item, f'warehouse_{warehouse.id}_qty', 0) or 0
                json_item['warehouses'][warehouse.code] = float(qty)
            
            json_data.append(json_item)
        
        return {
            'items': items_data,
            'json_data': json_data
        }
    
    def get_summary_statistics(self, stock_data):
        """Get summary statistics from processed data"""
        total_items = len(stock_data)
        total_stock_value = sum(item['total_quantity'] for item in stock_data)
        low_stock_count = sum(1 for item in stock_data if item['total_quantity'] < 10)
        active_warehouses = Warehouse.objects.filter(is_active=True).count()
        
        return {
            'total_items': total_items,
            'total_stock_value': total_stock_value,
            'low_stock_count': low_stock_count,
            'active_warehouses': active_warehouses,
        }


class StockItemDetailView(LoginRequiredMixin, TemplateView):
    """
    Stock Item Detail View
    
    Shows detailed lot information for a specific item across all warehouses.
    Displays lots with available quantity > 0 grouped by warehouse.
    """
    template_name = 'inventory/stock/stock-item-detail.html'
    
    def get_context_data(self, **kwargs):
        """Add item and warehouse lot data to context"""
        context = super().get_context_data(**kwargs)
        
        # Get the item
        item_id = self.kwargs.get('item_id')
        item = get_object_or_404(ItemSKU, id=item_id)
        context['item'] = item
        
        # Get lot data grouped by warehouse
        warehouse_lots = self.get_warehouse_lots(item)
        context['warehouse_lots'] = warehouse_lots
        
        # Get summary statistics for this item
        context.update(self.get_item_summary(warehouse_lots))
        
        return context
    
    def get_warehouse_lots(self, item):
        """
        Get lots for the item grouped by warehouse.
        Only includes lots with available_quantity > 0.
        """
        # Get all stocks for this item with available quantity
        stocks = Stock.objects.filter(
            item_sku=item,
            available_quantity__gt=0
        ).select_related('warehouse').order_by(
            'warehouse__name', 'lot_number'
        )
        
        # Group by warehouse
        warehouse_lots = {}
        for stock in stocks:
            warehouse = stock.warehouse
            if warehouse not in warehouse_lots:
                warehouse_lots[warehouse] = []
            
            warehouse_lots[warehouse].append({
                'stock': stock,
                'lot_number': stock.lot_number,
                'available_quantity': stock.available_quantity,
                'expiry_date': stock.expiry_date
            })
        
        return warehouse_lots
    
    def get_item_summary(self, warehouse_lots):
        """Get summary statistics for the item"""
        total_lots = sum(len(lots) for lots in warehouse_lots.values())
        total_available = sum(
            lot_data['available_quantity'] 
            for lots in warehouse_lots.values() 
            for lot_data in lots
        )
        warehouses_count = len(warehouse_lots)
        
        return {
            'total_lots': total_lots,
            'total_available': total_available,
            'warehouses_count': warehouses_count,
        }

