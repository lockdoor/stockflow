from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from production.views.dashboard import ProductionDashboardView
from production.views.production_order_views import (
    ProductionOrderCreateView, 
    ProductionOrderDetailView,
    ProductionOrderUpdateView,
    ProductionOrderDeleteView,
    ProductionOrderListView
)
app_name = 'production'

urlpatterns = [
    path('', ProductionDashboardView.as_view(), name='dashboard'),
    path('dashboard/', ProductionDashboardView.as_view(), name='dashboard'),
    path('production-order/<int:pk>/', ProductionOrderDetailView.as_view(), name='production-order-detail'),
    path('production-order/create/', ProductionOrderCreateView.as_view(), name='production-order-create'),
    path('production-order/<int:pk>/edit/', ProductionOrderUpdateView.as_view(), name='production-order-edit'),
    path('production-order/<int:pk>/delete/', ProductionOrderDeleteView.as_view(), name='production-order-delete'),
    path('production-order/', ProductionOrderListView.as_view(), name='production-order-list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)