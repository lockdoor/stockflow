# from catalog.views import category, item
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from catalog.views.category_views import (
    CategoryListView, CategoryIndexView, CategoryCreateView, CategoryUpdateView, CategoryDetailView
)

from catalog.views.item_views import (
    ItemListView, ItemCreateView, ItemUpdateView, ItemDetailView
)

from catalog.views.item_bom_views import ItemAutocompleteView

from catalog.views.bom_views import (
    BomListByParentIDView, BomCreateView, BomDeleteView
)

# namespaced URL patterns for the catalog app
app_name = 'catalog'

urlpatterns = [
    path('', ItemListView.as_view(), name='item-list'),
    path('items/', ItemListView.as_view(), name='item-list'),
    path('items/create/', ItemCreateView.as_view(), name='item-create'),
    path('items/<int:pk>/edit/', ItemUpdateView.as_view(), name='item-edit'),
    path('items/<int:pk>/detail/', ItemDetailView.as_view(), name='item-detail'),
    
    path('items-bom/<int:parent_id>/create', BomCreateView.as_view(), name='bom-create'),   
    path("items-bom/autocomplete/", ItemAutocompleteView.as_view(), name="item-bom-autocomplete"),
    path('items-bom/<int:parent_id>/boms', BomListByParentIDView.as_view(), name='bom-list'),
    path('bom/<int:pk>/delete/', BomDeleteView.as_view(), name='bom-delete'),
    
    path('categories/', CategoryIndexView.as_view(), name='category-index'),
    path('categories/list/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category-edit'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)