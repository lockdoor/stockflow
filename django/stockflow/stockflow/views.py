from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM
from inventory.models.stock import Stock
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement

@login_required
def dashboard_view(request):
    user = request.user
    
    # ดึงข้อมูลสถิติสำหรับ dashboard
    context = {
        'user': user,
        # Catalog Statistics
        'total_items': ItemSKU.objects.count(),
        'active_items': ItemSKU.objects.filter(status='ACTIVE').count(),
        'total_categories': Category.objects.count(),
        'total_boms': BOM.objects.count(),
        
        # Inventory Statistics
        'total_warehouses': Warehouse.objects.count(),
        'total_stock_records': Stock.objects.filter(available_quantity__gt=0).count(),
        'total_available_stock': Stock.objects.aggregate(
            total=Sum('available_quantity'))['total'] or 0,
        'recent_movements': StockMovement.objects.filter(
            status='COMPLETED').order_by('-created_at')[:5],
        'pending_movements': StockMovement.objects.filter(
            status='DRAFT').count(),
        
        # Low stock alerts (items with less than 10 units)
        'low_stock_items': Stock.objects.filter(
            available_quantity__lt=10, available_quantity__gt=0
        ).select_related('item_sku', 'warehouse').order_by('available_quantity')[:10],
        
        # Recent items
        'recent_items': ItemSKU.objects.order_by('-created_at')[:5],
    }

    if user.is_superuser:
        return render(request, 'dashboard/admin.html', context)
    else:
        return render(request, 'dashboard/general.html', context)
