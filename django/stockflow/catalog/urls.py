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

from catalog.views.image_views import (
    ItemImageCreateView,
    ItemImageBulkUploadView,
    ItemImageListView,
    ItemImageDetailView,
    ItemImageUpdateView,
    ItemImageDeleteView,
    ItemImageSetPrimaryView,
    ImageUploadProgressAPIView,
    ItemImagesAPIView,
)

from catalog.views.dashboard import catalog_dashboard_view

# namespaced URL patterns for the catalog app
app_name = 'catalog'

urlpatterns = [
    path('', catalog_dashboard_view, name='dashboard'),
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
    
        # Image management
    path('items/<int:item_id>/images/upload/', ItemImageCreateView.as_view(), name='image-upload'),
    path('items/<int:item_id>/images/bulk-upload/', ItemImageBulkUploadView.as_view(), name='image-bulk-upload'),
    path('items/<int:item_id>/images/', ItemImageListView.as_view(), name='image-list'),
    path('images/<int:pk>/', ItemImageDetailView.as_view(), name='image-detail'),
    path('images/<int:pk>/edit/', ItemImageUpdateView.as_view(), name='image-edit'),
    path('images/<int:pk>/delete/', ItemImageDeleteView.as_view(), name='image-delete'),
    path('images/<int:pk>/set-primary/', ItemImageSetPrimaryView.as_view(), name='image-set-primary'),
    
    # API endpoints
    path('api/images/upload-progress/', ImageUploadProgressAPIView.as_view(), name='image-upload-progress-api'),
    path('api/items/<int:pk>/images/', ItemImagesAPIView.as_view(), name='item-images-api'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)