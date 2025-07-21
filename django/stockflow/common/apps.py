"""
Common App Configuration

Configuration for the common app that provides shared utilities
and base classes for all StockFlow applications.
"""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = 'Common Utilities'
