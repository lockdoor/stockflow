from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from datetime import datetime, timedelta

from catalog.models.category import Category
from catalog.models.item import ItemSKU
from catalog.models.bom import BOM


@login_required
def catalog_dashboard_view(request):
    """
    Catalog-specific dashboard with detailed statistics and insights
    """
    # Basic Statistics
    total_items = ItemSKU.objects.count()
    active_items = ItemSKU.objects.filter(status='ACTIVE').count()
    draft_items = ItemSKU.objects.filter(status='DRAFT').count()
    inactive_items = ItemSKU.objects.filter(status='INACTIVE').count()
    
    # Categories
    total_categories = Category.objects.count()
    categories_with_items = Category.objects.annotate(
        items_count=Count('items')
    ).filter(items_count__gt=0).count()
    
    # BOMs
    total_boms = BOM.objects.count()
    # Remove the line that tries to filter by status since BOM doesn't have status field
    # active_boms = BOM.objects.filter(status='ACTIVE').count()
    
    # Recent Activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_additions = ItemSKU.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Recent Items
    recent_items = ItemSKU.objects.select_related('category').order_by('-created_at')[:10]
    
    # Categories breakdown
    categories_breakdown = Category.objects.annotate(
        items_count=Count('items'),
        active_items_count=Count('items', filter=Q(items__status='ACTIVE'))
    ).order_by('-items_count')[:8]
    
    # Items by Type
    items_by_type = ItemSKU.objects.values('type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Items needing attention (drafts or inactive)
    items_needing_attention = ItemSKU.objects.filter(
        Q(status='DRAFT') | Q(status='INACTIVE')
    ).select_related('category')[:10]
    
    # BOMs breakdown - count unique parent SKUs that have BOMs
    boms_with_components = BOM.objects.values('parent_sku').distinct().count()
    
    context = {
        # Basic Stats
        'total_items': total_items,
        'active_items': active_items,
        'draft_items': draft_items,
        'inactive_items': inactive_items,
        'total_categories': total_categories,
        'categories_with_items': categories_with_items,
        'total_boms': total_boms,
        'boms_with_components': boms_with_components,
        
        # Activity
        'recent_additions': recent_additions,
        'recent_items': recent_items,
        'categories_breakdown': categories_breakdown,
        'items_by_type': items_by_type,
        'items_needing_attention': items_needing_attention,
        
        # Calculated percentages
        'active_items_percentage': round((active_items / total_items * 100) if total_items > 0 else 0, 1),
        'categories_utilization': round((categories_with_items / total_categories * 100) if total_categories > 0 else 0, 1),
    }
    
    return render(request, 'catalog/dashboard.html', context)
