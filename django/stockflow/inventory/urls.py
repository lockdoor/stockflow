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
    StockItemMovementCreateView,
    StockItemMovementDeleteView,
    StockItemMovementUpdateView,
    StockMovementItemProductionCreateView
)

from inventory.views.stock_view import (
    StockOverviewView,
    StockItemDetailView,
    StockItemMovementHistoryView
)

from inventory.views.stock_alert_views import (
    StockAlertListView,
    StockAlertDetailView,
    StockAlertCreateView,
    StockAlertUpdateView,
    StockAlertDeleteView,
    StockAlertBulkActionView,
    StockAlertToggleView
)

from inventory.views.reservation_views import (
    MaterialOverReservationListView
)

# namespaced URL patterns for the inventory app
app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', inventory_dashboard_view, name='dashboard'),
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
    path('stockmovement/history/', 
        StockMovementListView.as_view(), 
        name='stock-movement-history'),
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
    path('movement/<int:stock_movement_id>/production-form/',
        StockMovementItemProductionCreateView.as_view(),
        name='movement-production-create'),

    # Stock overview
    path('stock/overview/', StockOverviewView.as_view(), name='stock-overview'),
    path('stock/item/<int:item_id>/', StockItemDetailView.as_view(), name='stock-item-detail'),
    path('stock/item/<int:item_id>/history/', StockItemMovementHistoryView.as_view(), name='stock-item-movement-history'),

    # Stock alerts
    path('stock-alerts/', StockAlertListView.as_view(), name='stock-alert-list'),
    path('stock-alerts/<int:pk>/', StockAlertDetailView.as_view(), name='stock-alert-detail'),
    path('stock-alerts/create/', StockAlertCreateView.as_view(), name='stock-alert-create'),
    path('stock-alerts/<int:pk>/edit/', StockAlertUpdateView.as_view(), name='stock-alert-edit'),
    path('stock-alerts/<int:pk>/delete/', StockAlertDeleteView.as_view(), name='stock-alert-delete'),
    path('stock-alerts/bulk-action/', StockAlertBulkActionView.as_view(), name='stock-alert-bulk-action'),
    path('stock-alerts/<int:pk>/toggle/', StockAlertToggleView.as_view(), name='stock-alert-toggle'),

     # Reservation
    path('reservations/over/', 
        MaterialOverReservationListView.as_view(), 
        name='material-over-reservation-list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
