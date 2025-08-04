"""
Item Tests

Tests for item subdomain including model, form, and view tests.
Organized by domain-driven design principles.

Author: StockFlow Team
Created: 2025
"""

# Import all view tests for easy test discovery
from .test_item_list_view import ItemListViewTest
from .test_item_create_view import ItemCreateViewTest
from .test_item_update_view import ItemUpdateViewTest
from .test_item_detail_view import ItemDetailViewTest

__all__ = [
    'ItemListViewTest',
    'ItemCreateViewTest', 
    'ItemUpdateViewTest',
    'ItemDetailViewTest',
]
