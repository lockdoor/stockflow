# from catalog.views import category, item
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from catalog.views.category_views import (
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDetailView, CategoryDeleteView
)

from catalog.views.item_views import (
    ItemListView, ItemCreateView, ItemUpdateView, ItemDetailView
)

from catalog.views.bom_views import (
    BomListByParentIDView, BomCreateView, BomUpdateView, BomDeleteView
)

from catalog.views.dashboard import catalog_dashboard_view

# namespaced URL patterns for the catalog app
app_name = 'catalog'

urlpatterns = [
    path('dashboard/', catalog_dashboard_view, name='dashboard'),
    
    path('items/new/', ItemCreateView.as_view(), name='item-form'),
    path('items/<int:pk>/edit/', ItemUpdateView.as_view(), name='item-edit-form'),
    path('items/', ItemListView.as_view(), name='item-list'),
    path('items/<int:pk>/detail/', ItemDetailView.as_view(), name='item-detail'),
    
    path('bom/<int:parent_id>/create', BomCreateView.as_view(), name='bom-create'),
    path('bom/<int:parent_id>/list', BomListByParentIDView.as_view(), name='bom-list'),
    path('bom/<int:pk>/edit/', BomUpdateView.as_view(), name='bom-edit'),
    path('bom/<int:pk>/delete/', BomDeleteView.as_view(), name='bom-delete'),
    
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category-edit'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)