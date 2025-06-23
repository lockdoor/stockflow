from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# namespaced URL patterns for the catalog app
app_name = 'catalog'

urlpatterns = [
    path('create_raw_item', views.create_raw_item_view, name='create_raw_item'),
    path('items', views.items_view, name='items'),
    path('create_category', views.create_category_view, name='create_category'),
    path('categories', views.categories_view, name='categories')
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)