"""
StockMovementImage Model

This module defines the StockMovementImage model using mixins for clean separation of concerns.
Uses AuditableMixin for audit fields and optimistic locking,
and ValidatableMixin for validation framework.

Used to store document images for stock movements such as:
- Inbound receipts and delivery documents
- Outbound shipping documents  
- Adjustment supporting documents
- Production order documents

Author: StockFlow Team
Created: 2025
"""

import os
import uuid
from django.db import models, transaction
from django.core.exceptions import ValidationError
from inventory.models.stock_movement import StockMovement
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin


def upload_stock_movement_image_path(instance, filename):
    """
    Generate custom upload path for stock movement images.
    Format: stock_movement_images/movement_[movement_id]_image_[uuid].[extension]
    
    Args:
        instance: StockMovementImage instance
        filename: Original filename
        
    Returns:
        str: Custom file path
    """
    # Get file extension
    ext = filename.split('.')[-1].lower()
    
    # Generate unique identifier for the image
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    
    # Create custom filename: movement_[movement_id]_image_[unique_id].[ext]
    custom_filename = f"movement_{instance.stock_movement.id}_image_{unique_id}.{ext}"
    
    # Return full path: stock_movement_images/movement_1_image_a1b2c3d4.jpg
    return os.path.join('stock_movement_images', custom_filename)


from inventory.validators.stock_movement_image_validators import (
    StockMovementImageValidator,
    StockMovementImagePrimaryValidator,
    StockMovementImageBusinessRulesValidator
)


class StockMovementImage(AuditableMixin, ValidatableMixin, models.Model):
    """
    StockMovementImage model for managing stock movement document images.
    Used to store supporting documents for stock movements such as receipts,
    delivery documents, adjustment forms, etc.
    
    Uses mixins for audit fields and validation framework.
    """
    
    # Core fields
    stock_movement = models.ForeignKey(
        StockMovement, 
        on_delete=models.CASCADE, 
        related_name='images',
        help_text="The stock movement this image belongs to"
    )
    image = models.FileField(
        upload_to=upload_stock_movement_image_path,
        help_text="Document image or PDF file for the stock movement"
    )
    caption = models.CharField(
        max_length=255, 
        blank=True, 
        default='',
        help_text="Optional caption describing the document (e.g., 'Receipt', 'Delivery Note')"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as primary document image for the stock movement"
    )
    note = models.TextField(
        blank=True,
        default='',
        help_text="Additional notes about the document or image"
    )

    class Meta:
        db_table = 'inventory_stockmovementimage'
        verbose_name = 'Stock Movement Image'
        verbose_name_plural = 'Stock Movement Images'
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['stock_movement']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            # Allow manual validation for primary image constraint
            # models.UniqueConstraint(
            #     fields=['stock_movement'],
            #     condition=models.Q(is_primary=True),
            #     name='unique_primary_image_per_stock_movement'
            # )
        ]

    def __str__(self):
        primary_text = " (Primary)" if self.is_primary else ""
        caption_text = f" - {self.caption}" if self.caption else ""
        return f"Movement {self.stock_movement.id} Image{caption_text}{primary_text}"

    def get_validators(self):
        """Return list of validators for this stock movement image"""
        return [
            StockMovementImageValidator(self),
            StockMovementImagePrimaryValidator(self),
            StockMovementImageBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """Save with validation and field normalization"""
        # Normalize text fields
        if self.caption:
            self.caption = self.caption.strip()
        if self.note:
            self.note = self.note.strip()
            
        # Ensure only one primary image per stock movement
        if self.is_primary:
            with transaction.atomic():
                # Set all other images for this stock movement to non-primary
                qs = self.__class__.objects.filter(stock_movement=self.stock_movement, is_primary=True)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                qs.update(is_primary=False)
        
        # Run validation through mixins
        self.full_clean()
        
        # Call parent save (includes optimistic locking)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete with file cleanup"""
        # Store image path before deletion
        image_path = self.image.path if self.image else None
        
        # Delete the model instance
        super().delete(*args, **kwargs)
        
        # Clean up the file from filesystem
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass  # File might already be deleted or permission issues

    @property
    def file_size(self):
        """Get file size in bytes"""
        try:
            return self.image.size if self.image else 0
        except (OSError, ValueError):
            return 0

    @property
    def file_name(self):
        """Get original file name"""
        return os.path.basename(self.image.name) if self.image else ''