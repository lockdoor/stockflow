from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from inventory.views.warehouse_views import (
    WarehouseListView, WarehouseDetailView, 
    WarehouseCreateView, WarehouseUpdateView
)

from inventory.views.stock_views import (
    StockMovementCreateView, 
    StockMovementByWareHouseListView, 
    StockMovementDeleteView, 
    StockMovementUpdateView
)

# namespaced URL patterns for the inventory app
app_name = 'inventory'

urlpatterns = [
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('warehouses/create/', WarehouseCreateView.as_view(), name='warehouse-create'),
    path('warehouses/edit/<int:pk>/', WarehouseUpdateView.as_view(), name='warehouse-edit'),
    
    path('warehouses/<int:warehouse_id>/stock-movements/', 
        StockMovementByWareHouseListView.as_view(), 
        name='stock-movement-list'),
    path('stockmovement/<int:warehouse_id>/create/', 
         StockMovementCreateView.as_view(), 
         name='stock-movement-create'),
    path('stockmovement/<int:pk>/delete/', 
        StockMovementDeleteView.as_view(), 
        name='stock-movement-delete'),
    path('stockmovement/<int:pk>/edit/', 
         StockMovementUpdateView.as_view(), 
         name='stock-movement-edit'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)