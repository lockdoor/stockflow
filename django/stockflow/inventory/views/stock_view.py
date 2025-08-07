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
from inventory.models.stock_alert import StockAlert
from inventory.models.stock_movement_item import StockMovementItem
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
        from inventory.models.stock_alert import StockAlert
        
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
        
        # Get all stock alerts for efficiency
        alerts_by_item = {}
        alerts = StockAlert.objects.filter(
            item_sku__in=items_queryset,
            is_enabled=True
        ).select_related('item_sku', 'warehouse')
        
        for alert in alerts:
            if alert.item_sku.id not in alerts_by_item:
                alerts_by_item[alert.item_sku.id] = []
            alerts_by_item[alert.item_sku.id].append(alert)
        
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
            
            # Get alert levels for this item
            item_alerts = alerts_by_item.get(item.id, [])
            alert_levels = [alert.get_alert_level() for alert in item_alerts]
            has_critical_alert = 'critical' in alert_levels
            has_warning_alert = 'warning' in alert_levels
            
            # Template data structure (keeping compatibility)
            item_data = {
                'item': item,
                'warehouses': warehouses_data,
                'total_quantity': item.total_quantity or 0,
                'has_critical_alert': has_critical_alert,
                'has_warning_alert': has_warning_alert,
                'alert_levels': alert_levels
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
                'has_critical_alert': has_critical_alert,
                'has_warning_alert': has_warning_alert,
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
        """Get summary statistics from processed data with stock alert levels"""
        from inventory.models.stock_alert import StockAlert
        
        total_items = len(stock_data)
        total_stock_value = sum(item['total_quantity'] for item in stock_data)
        
        # Count stock alert levels based on actual alert configurations
        warning_count = 0
        critical_count = 0
        
        for item_data in stock_data:
            item = item_data['item']
            # Check alerts for this item across all warehouses
            alerts = StockAlert.objects.filter(
                item_sku=item,
                is_enabled=True
            ).select_related('warehouse')
            
            for alert in alerts:
                alert_level = alert.get_alert_level()
                if alert_level == 'critical':
                    critical_count += 1
                elif alert_level == 'warning':
                    warning_count += 1
        
        active_warehouses = Warehouse.objects.filter(is_active=True).count()
        
        return {
            'total_items': total_items,
            'total_stock_value': total_stock_value,
            'warning_stock_count': warning_count,
            'critical_stock_count': critical_count,
            'low_stock_count': warning_count + critical_count,  # Keep backward compatibility
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
        
        # Get all stock alerts for this item in one query
        alerts_by_warehouse = {}
        alerts = StockAlert.objects.filter(
            item_sku=item
        ).select_related('warehouse')
        
        for alert in alerts:
            alerts_by_warehouse[alert.warehouse.id] = alert
        
        # Group by warehouse
        warehouse_lots = {}
        for stock in stocks:
            warehouse = stock.warehouse
            if warehouse not in warehouse_lots:
                # Attach existing alert if any
                warehouse.existing_alert = alerts_by_warehouse.get(warehouse.id)
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


class StockItemMovementHistoryView(LoginRequiredMixin, TemplateView):
    """
    Stock Item Movement History View
    
    Shows movement history (IN/OUT transactions) for a specific item,
    optionally filtered by warehouse and/or lot number.
    """
    template_name = 'inventory/stock/stock-item-movement-history.html'
    
    def get_context_data(self, **kwargs):
        """Add item and movement history to context"""
        context = super().get_context_data(**kwargs)
        
        # Get the item
        item_id = self.kwargs.get('item_id')
        item = get_object_or_404(ItemSKU, id=item_id)
        context['item'] = item
        
        # Get movement items for this item
        movement_items = self.get_movement_items(item)
        context['movement_items'] = movement_items
        
        # Get filter parameters
        warehouse_id = self.request.GET.get('warehouse')
        lot_number = self.request.GET.get('lot')
        
        context['warehouse_filter'] = warehouse_id
        context['lot_filter'] = lot_number
        
        # Get warehouse name if filtered
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
                context['warehouse_name'] = warehouse.name
            except Warehouse.DoesNotExist:
                pass
        
        return context
    
    def get_movement_items(self, item):
        """
        Get movement items for the item, optionally filtered by warehouse and lot.
        """
        # Base query for movement items of this item
        movement_items = StockMovementItem.objects.filter(
            item_sku=item
        ).select_related(
            'stock_movement',
            'stock_movement__warehouse',
            'item_sku'
        ).order_by('-stock_movement__created_at', '-created_at')
        
        # Apply warehouse filter if provided and valid
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            try:
                # Check if warehouse exists before filtering
                warehouse_exists = Warehouse.objects.filter(id=warehouse_id).exists()
                if warehouse_exists:
                    movement_items = movement_items.filter(
                        stock_movement__warehouse_id=warehouse_id
                    )
            except (ValueError, TypeError):
                # Invalid warehouse ID format, skip filtering
                pass
        
        # Apply lot filter if provided
        lot_number = self.request.GET.get('lot')
        if lot_number:
            movement_items = movement_items.filter(
                lot_number=lot_number
            )
        
        return movement_items

