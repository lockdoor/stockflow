"""
Base Validator

This module contains the base validator class for all model validators.
Provides common structure and interface for validation logic.

Author: StockFlow Team
Created: 2025
"""

from abc import ABC, abstractmethod
from django.core.exceptions import ValidationError


class BaseValidator(ABC):
    """Base class for all model validators"""
    
    def __init__(self, instance):
        """Initialize validator with model instance"""
        self.instance = instance
    
    @abstractmethod
    def validate(self):
        """
        Validate the model instance.
        Must return a list of ValidationError objects.
        """
        pass
    
    def is_valid(self):
        """Check if validation passes"""
        errors = self.validate()
        return len(errors) == 0
    
    def get_errors(self):
        """Get validation errors"""
        return self.validate()
