"""
Base Validators

Common validation classes that can be extended by specific model validators.
Provides reusable validation patterns for common field types and business rules.

Author: StockFlow Team
Created: 2025
"""

import re
from django.core.exceptions import ValidationError


class BaseFieldValidator:
    """Base class for field validators"""
    
    def __init__(self, instance, field_name):
        self.instance = instance
        self.field_name = field_name
        self.field_value = getattr(instance, field_name, None)
    
    def validate(self):
        """Override in subclasses"""
        return None


class RequiredFieldValidator(BaseFieldValidator):
    """Validator for required fields"""
    
    def __init__(self, instance, field_name, custom_message=None):
        super().__init__(instance, field_name)
        self.custom_message = custom_message
    
    def validate(self):
        if not self.field_value or (isinstance(self.field_value, str) and not self.field_value.strip()):
            return self.custom_message or f"{self.field_name.replace('_', ' ').title()} is required"
        return None


class LengthValidator(BaseFieldValidator):
    """Validator for field length constraints"""
    
    def __init__(self, instance, field_name, min_length=None, max_length=None):
        super().__init__(instance, field_name)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self):
        if not self.field_value:
            return None
        
        value_length = len(str(self.field_value).strip())
        
        if self.min_length and value_length < self.min_length:
            return f"{self.field_name.replace('_', ' ').title()} must be at least {self.min_length} characters"
        
        if self.max_length and value_length > self.max_length:
            return f"{self.field_name.replace('_', ' ').title()} cannot exceed {self.max_length} characters"
        
        return None


class RegexValidator(BaseFieldValidator):
    """Validator for regex pattern matching"""
    
    def __init__(self, instance, field_name, pattern, message):
        super().__init__(instance, field_name)
        self.pattern = pattern
        self.message = message
    
    def validate(self):
        if not self.field_value:
            return None
        
        if not re.match(self.pattern, str(self.field_value)):
            return self.message
        
        return None


class UniqueFieldValidator(BaseFieldValidator):
    """Validator for unique field constraints"""
    
    def __init__(self, instance, field_name, case_sensitive=True):
        super().__init__(instance, field_name)
        self.case_sensitive = case_sensitive
    
    def validate(self):
        if not self.field_value:
            return None
        
        # Get the model class
        model_class = self.instance.__class__
        
        # Build query filter
        if self.case_sensitive:
            filter_kwargs = {self.field_name: self.field_value}
        else:
            filter_kwargs = {f"{self.field_name}__iexact": self.field_value}
        
        # Check for existing records
        existing = model_class.objects.filter(**filter_kwargs)
        
        # Exclude current instance if updating
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            return f"{self.field_name.replace('_', ' ').title()} '{self.field_value}' already exists"
        
        return None


class CodeFormatValidator(BaseFieldValidator):
    """Validator for code format (alphanumeric codes)"""
    
    def __init__(self, instance, field_name, min_length=2, max_length=10):
        super().__init__(instance, field_name)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self):
        if not self.field_value:
            return None
        
        # Check format (alphanumeric only)
        pattern = f'^[A-Za-z0-9]{{{self.min_length},{self.max_length}}}$'
        if not re.match(pattern, str(self.field_value)):
            return f"{self.field_name.replace('_', ' ').title()} must be {self.min_length}-{self.max_length} alphanumeric characters"
        
        return None
