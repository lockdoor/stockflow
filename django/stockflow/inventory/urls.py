from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from inventory.views.warehouse_views import (
    WarehouseListView, WarehouseDetailView, WarehouseCreateView, WarehouseUpdateView
)

# namespaced URL patterns for the inventory app
app_name = 'inventory'

urlpatterns = [
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('warehouses/create/', WarehouseCreateView.as_view(), name='warehouse-create'),
    path('warehouses/edit/<int:pk>/', WarehouseUpdateView.as_view(), name='warehouse-edit'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)