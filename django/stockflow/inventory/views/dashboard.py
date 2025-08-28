from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem

from inventory.models.stock import Stock
from inventory.models.material_reservation import MaterialReservation


@login_required
def inventory_dashboard_view(request):
    """
    Inventory-specific dashboard with detailed statistics and insights
    """
    # Basic Statistics
    total_warehouses = Warehouse.objects.count()
    active_warehouses = Warehouse.objects.filter(is_active=True).count()
    
    total_movements = StockMovement.objects.count()
    completed_movements = StockMovement.objects.filter(status='COMPLETED').count()
    processing_movements = StockMovement.objects.filter(status='PROCESSING').count()
    draft_movements = StockMovement.objects.filter(status='DRAFT').count()
    
    total_stock_records = Stock.objects.count()
    available_stock_records = Stock.objects.filter(available_quantity__gt=0).count()
    
    # Total stock units
    total_stock_units = Stock.objects.aggregate(
        total=Sum('available_quantity')
    )['total'] or 0
    
    # Low stock alerts (less than 10 units per item per warehouse)
    low_stock_items = Stock.get_all_stock().filter(total_quantity__lt=10).count()
    
    # Recent movements (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_movements = StockMovement.objects.filter(
        created_at__gte=week_ago
    ).select_related('warehouse', 'created_by').order_by('-created_at')[:8]
    
    # Movement status breakdown
    movements_by_status = StockMovement.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Items needing attention (movements in PROCESSING or FAILED status)
    items_needing_attention = StockMovement.objects.filter(
        status__in=['PROCESSING', 'FAILED']
    ).select_related('warehouse', 'created_by')[:8]
    

    # Stock by warehouse with reservation summary
    stock_by_warehouse = []
    warehouses = Warehouse.objects.filter(is_active=True)
    for warehouse in warehouses:
        items_count = warehouse.stocks.values('item_sku').distinct().count()
        total_quantity = warehouse.stocks.aggregate(total=Sum('available_quantity'))['total'] or 0
        reserved_quantity = MaterialReservation.objects.filter(
            warehouse=warehouse,
            status=MaterialReservation.Status.RESERVED
        ).aggregate(total=Sum('reserved_quantity'))['total'] or 0
        available_after_reservation = total_quantity - reserved_quantity
        stock_by_warehouse.append({
            'id': warehouse.id,
            'name': warehouse.name,
            'code': warehouse.code,
            'items_count': items_count,
            'total_quantity': total_quantity,
            'reserved_quantity': reserved_quantity,
            'available_after_reservation': available_after_reservation,
        })
    # Sort by total_quantity desc, limit 8
    stock_by_warehouse = sorted(stock_by_warehouse, key=lambda w: w['total_quantity'], reverse=True)[:8]
    
    # Recent activity count
    recent_movements_count = StockMovement.objects.filter(
        created_at__gte=week_ago
    ).count()
    
    # Calculate percentages
    completed_percentage = round((completed_movements / total_movements * 100) if total_movements > 0 else 0, 1)
    active_warehouses_percentage = round((active_warehouses / total_warehouses * 100) if total_warehouses > 0 else 0, 1)
    stock_utilization = round((available_stock_records / total_stock_records * 100) if total_stock_records > 0 else 0, 1)
    
    context = {
        # Basic stats
        'total_warehouses': total_warehouses,
        'active_warehouses': active_warehouses,
        'active_warehouses_percentage': active_warehouses_percentage,
        'total_movements': total_movements,
        'completed_movements': completed_movements,
        'completed_percentage': completed_percentage,
        'processing_movements': processing_movements,
        'draft_movements': draft_movements,
        'total_stock_records': total_stock_records,
        'available_stock_records': available_stock_records,
        'stock_utilization': stock_utilization,
        'total_stock_units': total_stock_units,
        'low_stock_items': low_stock_items,
        'recent_movements_count': recent_movements_count,
        
        # Recent data
        'recent_movements': recent_movements,
        'movements_by_status': movements_by_status,
        'items_needing_attention': items_needing_attention,
        'stock_by_warehouse': stock_by_warehouse,
    }
    
    return render(request, 'inventory/dashboard.html', context)
