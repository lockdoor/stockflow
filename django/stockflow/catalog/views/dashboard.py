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
    active_categories = Category.objects.filter(is_active=True).count()
    categories_with_items = Category.objects.annotate(
        items_count=Count('items')
    ).filter(items_count__gt=0).count()
    
    # BOMs
    total_boms = BOM.objects.count()
    boms_with_items = BOM.objects.values('parent_sku').distinct().count()
    
    # Items with images (assuming there's an image field or related model)
    # For now, we'll use a placeholder since we don't see image model
    items_with_images = 0  # TODO: Update when image model is available
    image_coverage_percentage = round((items_with_images / total_items * 100) if total_items > 0 else 0, 1)
    
    # Recent Activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_additions = ItemSKU.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Recent Items (for dashboard display) - optimized with prefetch
    recent_items = ItemSKU.objects.select_related('category').prefetch_related('bom_parent').order_by('-created_at')[:5]
    
    # Categories with counts for dashboard display
    categories_with_counts = Category.objects.annotate(
        item_count=Count('items')
    ).filter(item_count__gt=0).order_by('-item_count')[:6]
    
    # If no categories have items, show all categories
    if not categories_with_counts.exists():
        categories_with_counts = Category.objects.annotate(
            item_count=Count('items')
        ).order_by('name')[:6]
    
    # Categories breakdown for detailed analysis
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
    
    context = {
        # Statistics for template cards
        'total_items': total_items,
        'recent_additions': recent_additions,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'total_boms': total_boms,
        'boms_with_items': boms_with_items,
        'items_with_images': items_with_images,
        'image_coverage_percentage': image_coverage_percentage,
        
        # Dashboard sections
        'categories_with_counts': categories_with_counts,
        'recent_items': recent_items,
        
        # Detailed stats (for potential use)
        'active_items': active_items,
        'draft_items': draft_items,
        'inactive_items': inactive_items,
        'categories_with_items': categories_with_items,
        'categories_breakdown': categories_breakdown,
        'items_by_type': items_by_type,
        'items_needing_attention': items_needing_attention,
        
        # Calculated percentages
        'active_items_percentage': round((active_items / total_items * 100) if total_items > 0 else 0, 1),
        'categories_utilization': round((categories_with_items / total_categories * 100) if total_categories > 0 else 0, 1),
    }
    
    return render(request, 'catalog/dashboard.html', context)
