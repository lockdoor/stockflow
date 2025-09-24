"""
Stock Movement Image Validators

This module contains validators for the StockMovementImage model.
Provides comprehensive validation for image uploads, business rules,
and data integrity for stock movement documentation.

Author: StockFlow Team  
Created: 2025
"""

import os
from django.core.exceptions import ValidationError
from common.validators.base import BaseValidator


class StockMovementImageValidator(BaseValidator):
    """Validator for basic stock movement image fields"""
    
    def validate(self):
        """Validate stock movement image basic fields"""
        errors = []
        
        # Check if stock_movement is provided
        if not self.instance.stock_movement:
            errors.append("Stock movement is required.")
            return errors
        
        # Check if image is provided
        if not self.instance.image:
            errors.append("Image file is required.")
            return errors
        
        # Validate image file
        try:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if self.instance.image.size > max_size:
                errors.append(f"Image file size cannot exceed 10MB. Current size: {self.instance.image.size / (1024*1024):.1f}MB")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf']
            file_name = self.instance.image.name.lower()
            file_ext = os.path.splitext(file_name)[1]
            
            if file_ext not in allowed_extensions:
                errors.append(f"File type '{file_ext}' is not supported. Allowed types: {', '.join(allowed_extensions)}")
                
        except (AttributeError, ValueError) as e:
            errors.append(f"Invalid image file: {str(e)}")
        
        return errors


class StockMovementImagePrimaryValidator(BaseValidator):
    """Validator for primary image business rules"""
    
    def validate(self):
        """Validate primary image constraints"""
        errors = []
        
        # Only validate if this is marked as primary
        if not self.instance.is_primary:
            return errors
        
        # Check if stock movement exists
        if not self.instance.stock_movement:
            return errors
        
        # For updates, check if another primary image already exists
        if hasattr(self.instance, '_state') and not self.instance._state.adding:
            existing_primary = self.instance.__class__.objects.filter(
                stock_movement=self.instance.stock_movement,
                is_primary=True
            ).exclude(pk=self.instance.pk).first()
            
            if existing_primary:
                errors.append(
                    f"Stock movement already has a primary image. "
                    f"Please unmark the existing primary image first."
                )
        
        return errors


class StockMovementImageBusinessRulesValidator(BaseValidator):
    """Validator for stock movement image business rules"""
    
    def validate(self):
        """Validate business rules for stock movement images"""
        errors = []
        
        # Check if stock movement exists
        if not self.instance.stock_movement:
            return errors
        
        # Note field validation (basic length check)
        if self.instance.note and len(self.instance.note.strip()) > 1000:
            errors.append("Note cannot exceed 1000 characters.")
        
        # Validate caption length
        if self.instance.caption and len(self.instance.caption.strip()) > 255:
            errors.append("Caption cannot exceed 255 characters.")
        
        # Check maximum number of images per stock movement (limit to 10)
        if hasattr(self.instance, '_state') and self.instance._state.adding:
            existing_count = self.instance.__class__.objects.filter(
                stock_movement=self.instance.stock_movement
            ).count()
            
            if existing_count >= 10:
                errors.append(
                    "Maximum of 10 images allowed per stock movement. "
                    "Please delete some existing images before adding new ones."
                )
        
        # Validate stock movement status
        stock_movement = self.instance.stock_movement
        
        # Allow image upload for most statuses, but restrict for completed/cancelled
        restricted_statuses = []  # Can define restricted statuses if needed
        
        if hasattr(stock_movement, 'status') and stock_movement.status in restricted_statuses:
            errors.append(
                f"Cannot add/modify images for stock movement with status '{stock_movement.status}'"
            )
        
        return errors


class StockMovementImageImmutableFieldValidator(BaseValidator):
    """Validator for immutable fields in stock movement images"""
    
    def validate(self):
        """Validate that certain fields cannot be changed after creation"""
        errors = []
        
        # Skip validation for new instances
        if hasattr(self.instance, '_state') and self.instance._state.adding:
            return errors
        
        try:
            # Get the original instance from database
            original = self.instance.__class__.objects.get(pk=self.instance.pk)
            
            # Check if stock_movement was changed (should not be allowed)
            if self.instance.stock_movement_id != original.stock_movement_id:
                errors.append("Stock movement cannot be changed once the image is created.")
                
        except self.instance.__class__.DoesNotExist:
            errors.append("Stock movement image no longer exists.")
        
        return errors