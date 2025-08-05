"""
Context processors for adding common data to all templates
"""

from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404

def breadcrumb(request):
    """
    Generate breadcrumb navigation based on current URL
    """
    try:
        resolver_match = resolve(request.path)
        url_name = resolver_match.url_name
        namespace = resolver_match.namespace
        
        # Define breadcrumb mapping
        breadcrumb_map = {
            # Main dashboard
            'dashboard': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': True}
            ],
            
            # Catalog module
            'catalog:dashboard': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': True}
            ],
            'catalog:item-list': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Items', 'url': 'catalog:item-list', 'active': True}
            ],
            'catalog:item-form': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Items', 'url': 'catalog:item-list', 'active': False},
                {'name': 'New Item', 'url': None, 'active': True}
            ],
            'catalog:item-edit-form': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Items', 'url': 'catalog:item-list', 'active': False},
                {'name': 'Edit Item', 'url': None, 'active': True}
            ],
            'catalog:item-detail': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Items', 'url': 'catalog:item-list', 'active': False},
                {'name': 'Item Details', 'url': None, 'active': True}
            ],
            'catalog:bom-create': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Items', 'url': 'catalog:item-list', 'active': False},
                {'name': 'Item Details', 'url': reverse('catalog:item-detail', args=[resolver_match.kwargs.get('parent_id')]) if resolver_match.kwargs.get('parent_id') else None, 'active': False},
                {'name': 'Create BOM', 'url': None, 'active': True}
            ],
            'catalog:category-list': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Categories', 'url': 'catalog:category-list', 'active': True}
            ],
            'catalog:category-create': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Categories', 'url': 'catalog:category-list', 'active': False},
                {'name': 'New Category', 'url': None, 'active': True}
            ],
            'catalog:category-edit': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Categories', 'url': 'catalog:category-list', 'active': False},
                {'name': 'Edit Category', 'url': None, 'active': True}
            ],
            'catalog:category-detail': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Catalog', 'url': 'catalog:dashboard', 'active': False},
                {'name': 'Categories', 'url': 'catalog:category-list', 'active': False},
                {'name': 'Category Details', 'url': None, 'active': True}
            ],
            
            # Inventory module
            'inventory:dashboard': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Inventory', 'url': 'inventory:dashboard', 'active': True}
            ],
            'inventory:stock-movement-list': [
                {'name': 'Dashboard', 'url': 'dashboard', 'active': False},
                {'name': 'Inventory', 'url': 'inventory:dashboard', 'active': False},
                {'name': 'Stock Movements', 'url': 'inventory:stock-movement-list', 'active': True}
            ],
        }
        
        # Get breadcrumb for current URL
        full_url_name = f"{namespace}:{url_name}" if namespace else url_name
        breadcrumb_items = breadcrumb_map.get(full_url_name, [])
        
        return {
            'breadcrumb_items': breadcrumb_items,
            'current_url_name': full_url_name
        }
        
    except (Resolver404, AttributeError):
        return {
            'breadcrumb_items': [],
            'current_url_name': ''
        }
