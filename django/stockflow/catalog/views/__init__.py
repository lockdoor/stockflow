"""
Catalogfrom catalog.views.image_views import (
    ItemImageCreateView,
    ItemImageBulkUploadView,
    ItemImageListView,
    ItemImageDetailView,
    ItemImageUpdateView,
    ItemImageDeleteView,
    ItemImageSetPrimaryView,
    ImageUploadProgressAPIView,
    ItemImagesAPIView,
)age

This package contains all views for the catalog application.
Includes views for items, categories, BOMs, and images.

Author: StockFlow Team
Created: 2025
"""

# Import image views
from .image_views import (
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

__all__ = [
    # Image views (Class-based)
    'ItemImageCreateView',
    'ItemImageBulkUploadView',
    'ItemImageListView',
    'ItemImageDetailView',
    'ItemImageUpdateView',
    'ItemImageDeleteView',
    'ItemImageSetPrimaryView',
    'ImageUploadProgressAPIView',
    'ItemImagesAPIView',
]