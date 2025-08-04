from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from inventory.views.dashboard import inventory_dashboard_view

from inventory.views.warehouse_views import (
    WarehouseListView, WarehouseDetailView, 
    WarehouseCreateView, WarehouseUpdateView,
    WarehouseIndexView
)

from inventory.views.stock_movement_views import (
    StockMovementCreateView, 
    StockMovementByWarehouseListView, 
    StockMovementDeleteView, 
    StockMovementUpdateView,
    StockMovementDetailView,
    StockMovementConfirmView
)

from inventory.views.stock_item_views import (
     StockItemMovementListView,
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
         WarehouseIndexView.as_view(), 
         name='warehouse-index'),
    path('warehouses/list/', 
         WarehouseListView.as_view(), 
         name='warehouse-list'),
    path('warehouses/<int:pk>/', 
         WarehouseDetailView.as_view(), 
         name='warehouse-detail'),
    path('warehouses/create/', 
         WarehouseCreateView.as_view(), 
         name='warehouse-create'),
    path('warehouses/edit/<int:pk>/', 
         WarehouseUpdateView.as_view(), 
         name='warehouse-edit'),   
    
    # Warehouse stock movements
    path('warehouses/<int:warehouse_id>/stock-movements/', 
        StockMovementByWarehouseListView.as_view(), 
        name='stock-movement-list'), 
    path('warehouses/<int:warehouse_id>/stock-movements/create/', 
         StockMovementCreateView.as_view(), 
         name='stock-movement-create'),
    
    # Stock movement
    path('stockmovement/<int:pk>/', 
         StockMovementDetailView.as_view(), 
         name='stock-movement-detail'),
    path('stockmovement/<int:pk>/delete/', 
        StockMovementDeleteView.as_view(), 
        name='stock-movement-delete'),
    path('stockmovement/<int:pk>/edit/', 
         StockMovementUpdateView.as_view(), 
         name='stock-movement-edit'),
     path('stockmovement/<int:pk>/confirm/', 
          StockMovementConfirmView.as_view(), 
          name='stock-movement-confirm'),
    
    # Stock item movements
    path('stockmovement/<int:stock_movement_id>/items/', 
         StockItemMovementListView.as_view(), 
         name='stock-item-movement-list'),
    path('stockmovement/<int:stock_movement_id>/items/create/', 
         StockItemMovementCreateView.as_view(), 
         name='stock-item-movement-create'),
    path('stockmovement/<int:stock_movement_id>/items/<int:pk>/edit/', 
         StockItemMovementUpdateView.as_view(), 
         name='stock-item-movement-edit'),
     path('stockmovement/<int:stock_movement_id>/items/<int:pk>/delete/',
          StockItemMovementDeleteView.as_view(), 
          name='stock-item-movement-delete'),
     
     path('stock/', StockIndexView.as_view(), name='stock-index'),
     path('stock/list/', StockListView.as_view(), name='stock-list'),
     path('stock/items/', StockItemListView.as_view(), name='stock-item-list'),
     
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
