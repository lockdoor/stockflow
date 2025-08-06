from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from inventory.views.dashboard import inventory_dashboard_view

from inventory.views.warehouse_views import (
    WarehouseListView, WarehouseDetailView, 
    WarehouseCreateView, WarehouseUpdateView
)

from inventory.views.stock_movement_views import (
    StockMovementCreateView, 
    StockMovementListView,
    StockMovementDeleteView, 
    StockMovementUpdateView,
    StockMovementDetailView,
    StockMovementConfirmView
)

from inventory.views.stock_movement_item_views import (
     # StockItemMovementListView,
     StockItemMovementCreateView,
     StockItemMovementDeleteView,
     StockItemMovementUpdateView
)

from inventory.views.stock_view import (
     StockListView,
     StockIndexView,
     StockItemListView
)

# namespaced URL patterns for the inventory app
app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('dashboard/', inventory_dashboard_view, name='dashboard'),
    
    # Warehouse management
    path('warehouses/', 
         WarehouseListView.as_view(), 
         name='warehouse-list'),
    path('warehouses/<int:pk>/', 
         WarehouseDetailView.as_view(), 
         name='warehouse-detail'),
    path('warehouses/form/', 
         WarehouseCreateView.as_view(), 
         name='warehouse-form'),
    path('warehouses/<int:pk>/form/', 
         WarehouseUpdateView.as_view(), 
         name='warehouse-edit-form'),
    
    # Stock movement
    path('stockmovement/', 
         StockMovementListView.as_view(), 
         name='stock-movement-list'),
    path('stockmovement/<int:pk>/', 
         StockMovementDetailView.as_view(), 
         name='stock-movement-detail'),
    path('stockmovement/<int:pk>/delete/', 
        StockMovementDeleteView.as_view(), 
        name='stock-movement-delete'),
    path('stockmovement/create/', 
         StockMovementCreateView.as_view(), 
         name='stock-movement-create'),
    path('stockmovement/<int:pk>/edit/', 
         StockMovementUpdateView.as_view(), 
         name='stock-movement-update'),
     path('stockmovement/<int:pk>/confirm/', 
          StockMovementConfirmView.as_view(), 
          name='stock-movement-confirm'),
    
    # Stock item movements
    path('movement/<int:stock_movement_id>/form/', 
         StockItemMovementCreateView.as_view(),
         name='movement-create'),
    path('movement/<int:stock_movement_id>/items/<int:pk>/edit/', 
         StockItemMovementUpdateView.as_view(),
         name='movement-edit'),
    path('movement/<int:stock_movement_id>/items/<int:pk>/delete/', 
         StockItemMovementDeleteView.as_view(),
         name='movement-delete'),

     
     path('stock/', StockIndexView.as_view(), name='stock-index'),
     path('stock/list/', StockListView.as_view(), name='stock-list'),
     path('stock/items/', StockItemListView.as_view(), name='stock-item-list'),
     
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
