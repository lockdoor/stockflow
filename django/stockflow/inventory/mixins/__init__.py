"""
Inventory Mixins

Domain-specific mixins for inventory models.

Author: StockFlow Team
Created: 2025
"""

from .immutable import ImmutableMixin, StatusImmutableMixin, VersionedImmutableMixin

__all__ = [
    'ImmutableMixin',
    'StatusImmutableMixin', 
    'VersionedImmutableMixin'
]
