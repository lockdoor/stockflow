"""
ItemImage Validators

This module contains validators for ItemImage model.
Provides validation for image files, primary image constraints, and business rules.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from common.validators.base import BaseValidator
import os


class ItemImageValidator(BaseValidator):
    """Validator for basic ItemImage field validation"""
    
    def validate(self):
        """Validate basic image fields"""
        errors = []
        
        # Validate image file
        if self.instance.image:
            errors.extend(self._validate_image_file())
        
        # Validate caption
        if self.instance.caption:
            errors.extend(self._validate_caption())
            
        return errors
    
    def _validate_image_file(self):
        """Validate image file properties"""
        errors = []
        image = self.instance.image
        
        try:
            # Check if file exists and is readable
            if not image or not hasattr(image, 'file'):
                errors.append("Invalid image file")
                return errors
            
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if image.size > max_size:
                errors.append(
                    f"Image file too large. Maximum size is {max_size/1024/1024:.1f}MB"
                )
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_extension = os.path.splitext(image.name)[1].lower()
            if file_extension not in allowed_extensions:
                errors.append(
                    f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Check image dimensions
            try:
                width, height = get_image_dimensions(image)
                if width and height:
                    # Maximum dimensions: 4000x4000
                    max_dimension = 4000
                    if width > max_dimension or height > max_dimension:
                        errors.append(
                            f"Image dimensions too large. Maximum: {max_dimension}x{max_dimension}px"
                        )
                    
                    # Minimum dimensions: 50x50
                    min_dimension = 50
                    if width < min_dimension or height < min_dimension:
                        errors.append(
                            f"Image dimensions too small. Minimum: {min_dimension}x{min_dimension}px"
                        )
            except Exception:
                errors.append("Could not read image dimensions")
                
        except Exception as e:
            errors.append(f"Error validating image: {str(e)}")
        
        return errors
    
    def _validate_caption(self):
        """Validate image caption"""
        errors = []
        caption = self.instance.caption.strip() if self.instance.caption else ''
        
        if len(caption) > 255:
            errors.append("Caption cannot exceed 255 characters")
        
        return errors


class ItemImagePrimaryValidator(BaseValidator):
    """Validator for primary image constraints"""
    
    def validate(self):
        """Validate primary image business rules"""
        errors = []
        
        if self.instance.is_primary:
            errors.extend(self._validate_primary_constraint())
        
        return errors
    
    def _validate_primary_constraint(self):
        """Validate that only one primary image exists per item"""
        errors = []
        
        # Skip validation - handled in save() method
        return errors


class ItemImageBusinessRulesValidator(BaseValidator):
    """Validator for ItemImage business rules"""
    
    def validate(self):
        """Validate business rules for ItemImage"""
        errors = []
        
        # Validate item relationship
        errors.extend(self._validate_item_relationship())
        
        # Validate image limit per item
        errors.extend(self._validate_image_limit())
        
        return errors
    
    def _validate_item_relationship(self):
        """Validate item relationship"""
        errors = []
        
        # Safe check for item relationship
        try:
            item = self.instance.item
            if not item:
                errors.append("Item is required")
                return errors
        except:
            errors.append("Item is required")
            return errors
        
        # Check if item is active
        if hasattr(item, 'status') and item.status == 'INACTIVE':
            errors.append(
                "Cannot add images to inactive items"
            )
        
        return errors
    
    def _validate_image_limit(self):
        """Validate maximum number of images per item"""
        errors = []
        
        # Safe check for item
        try:
            item = self.instance.item
            if not item:
                return errors
        except:
            return errors
        
        # Maximum 10 images per item
        max_images = 10
        from catalog.models.image import ItemImage
        current_count = ItemImage.objects.filter(item=item).count()
        
        # If this is a new image (no pk), check if we're at the limit
        if not self.instance.pk and current_count >= max_images:
            errors.append(f"Maximum {max_images} images allowed per item")
        
        return errors
