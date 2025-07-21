"""
Validation Mixin

Provides extensible validation framework for models.
Allows for clean separation of validation logic from model definition.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError


class ValidatableMixin:
    """
    Mixin that provides extensible validation framework.
    
    Subclasses should override get_validators() to return list of validator instances.
    Each validator should have a validate() method that returns error string or None.
    """
    
    def get_validators(self):
        """
        Return list of validator instances for this model.
        
        Override in subclasses to add specific validators.
        Each validator should have a validate() method.
        
        Returns:
            list: List of validator instances
        """
        return []
    
    def clean(self):
        """
        Run all validators and raise ValidationError if any fail.
        
        This method is called by Django's full_clean() during form validation
        and can be called manually for validation.
        """
        super().clean() if hasattr(super(), 'clean') else None
        
        errors = []
        validators = self.get_validators()
        
        for validator in validators:
            if hasattr(validator, 'validate'):
                error = validator.validate()
                if error:
                    errors.append(error)
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    def is_valid(self):
        """
        Check if model instance is valid without raising exceptions.
        
        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        try:
            self.clean()
            return True, []
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                # Field-specific errors
                errors = []
                for field, messages in e.message_dict.items():
                    errors.extend([f"{field}: {msg}" for msg in messages])
                return False, errors
            else:
                # Non-field errors
                return False, e.messages if hasattr(e, 'messages') else [str(e)]
        except Exception as e:
            return False, [str(e)]
