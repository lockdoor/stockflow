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
    ProductionOrderCreatedStatusView,
    ProductionOrderDraftStatusView,
)
from production.views.wip_views import (
    WIPStockListView
)
from production.views.production_order_bom_views import (
    ProductionOrderBOMCreateView,
    ProductionOrderBOMUpdateView,
    ProductionOrderBOMDeleteView,
)
from production.views.production_process_unified import (
    ProductionProcessUnifiedView,
)
from production.views.production_process_views import (
    ProductionProcessDeleteView,
)
from production.views.production_process_detail import (
    ProductionProcessDetailView,
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
    path('production-order/<int:pk>/draft-status/', ProductionOrderDraftStatusView.as_view(), name='production-order-draft-status'),
    path('production-order/<int:pk>/wip-stock/', WIPStockListView.as_view(), name='wip-stock-list'),

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
    
    # production process unified
    path('production-order/<int:production_order_id>/process/unified/create/',
        ProductionProcessUnifiedView.as_view(),
        name='production-process-unified-create'),
    path('production-order/<int:production_order_id>/process/<int:process_id>/unified/edit/',
        ProductionProcessUnifiedView.as_view(),
        name='production-process-unified-edit'),
    path('production-order/<int:production_order_id>/process/<int:process_id>/unified/delete/',
        ProductionProcessDeleteView.as_view(),
        name='production-process-unified-delete'),
    path('production-order/<int:production_order_id>/process/<int:process_id>/',
        ProductionProcessDetailView.as_view(),
        name='production-process-detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)