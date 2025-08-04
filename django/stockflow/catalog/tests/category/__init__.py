"""
Test Suite for Category Module

This module provides a comprehensive test suite for the Category module.
Includes all test cases for models, forms, validators, and views.

Author: StockFlow Team
Created: 2025
"""

from .test_category_model import CategoryModelTest
from .test_category_forms import CategoryFormTest
from .test_category_validators import (
    CategoryNameValidatorTest,
    CategoryBusinessRulesValidatorTest,
    CategoryValidatorIntegrationTest
)
from .test_category_list_view import CategoryListViewTest
from .test_category_detail_view import CategoryDetailViewTest
from .test_category_create_view import CategoryCreateViewTest
from .test_category_update_view import CategoryUpdateViewTest
from .test_category_delete_view import CategoryDeleteViewTest

__all__ = [
    'CategoryModelTest',
    'CategoryFormTest', 
    'CategoryNameValidatorTest',
    'CategoryBusinessRulesValidatorTest',
    'CategoryValidatorIntegrationTest',
    'CategoryListViewTest',
    'CategoryDetailViewTest',
    'CategoryCreateViewTest',
    'CategoryUpdateViewTest',
    'CategoryDeleteViewTest'
]
