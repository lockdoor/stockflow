from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from production.views.dashboard import ProductionDashboardView
from production.views.production_order_views import (
    ProductionOrderCreateView, 
    ProductionOrderDetailView,
    ProductionOrderUpdateView,
    ProductionOrderDeleteView,
    ProductionOrderListView,
    ProductionOrderCreatedStatusView
)
from production.views.production_order_bom_views import (
    ProductionOrderBOMCreateView,
    ProductionOrderBOMUpdateView,
    ProductionOrderBOMDeleteView,
)
app_name = 'production'

urlpatterns = [
    path('', ProductionDashboardView.as_view(), name='dashboard'),
    path('dashboard/', ProductionDashboardView.as_view(), name='dashboard'),
    
    # production order
    path('production-order/<int:pk>/', ProductionOrderDetailView.as_view(), name='production-order-detail'),
    path('production-order/create/', ProductionOrderCreateView.as_view(), name='production-order-create'),
    path('production-order/<int:pk>/edit/', ProductionOrderUpdateView.as_view(), name='production-order-edit'),
    path('production-order/<int:pk>/delete/', ProductionOrderDeleteView.as_view(), name='production-order-delete'),
    path('production-order/', ProductionOrderListView.as_view(), name='production-order-list'),
    path('production-order/<int:pk>/created-status/', ProductionOrderCreatedStatusView.as_view(), name='production-order-created-status'),

    # production order bom
    path('production-order/<int:production_order_id>/add-bom/', 
        ProductionOrderBOMCreateView.as_view(), 
        name='production-order-add-bom'),
    path('production-order/<int:production_order_id>/bom/<int:pk>/edit/',
        ProductionOrderBOMUpdateView.as_view(),
        name='production-order-edit-bom'),
    path('production-order/<int:production_order_id>/bom/<int:pk>/delete/',
        ProductionOrderBOMDeleteView.as_view(),
        name='production-order-delete-bom'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)