"""
ItemImage Model

This module defines the ItemImage model using mixins for clean separation of concerns.
Uses AuditableMixin for audit fields and optimistic locking,
and ValidatableMixin for validation framework.

Author: StockFlow Team
Created: 2025
"""

import os
import uuid
from django.db import models, transaction
from django.core.exceptions import ValidationError
from catalog.models.item import ItemSKU
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin


def upload_item_image_path(instance, filename):
    """
    Generate custom upload path for item images.
    Format: item_images/item_[item_id]_image_[uuid].[extension]
    
    Args:
        instance: ItemImage instance
        filename: Original filename
        
    Returns:
        str: Custom file path
    """
    # Get file extension
    ext = filename.split('.')[-1].lower()
    
    # Generate unique identifier for the image
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    
    # Create custom filename: item_[item_id]_image_[unique_id].[ext]
    custom_filename = f"item_{instance.item.id}_image_{unique_id}.{ext}"
    
    # Return full path: item_images/item_1_image_a1b2c3d4.jpg
    return os.path.join('item_images', custom_filename)
from catalog.validators.image_validators import (
    ItemImageValidator,
    ItemImagePrimaryValidator,
    ItemImageBusinessRulesValidator
)


class ItemImage(AuditableMixin, ValidatableMixin, models.Model):
    """
    ItemImage model for managing item images with validation and audit trail.
    Uses mixins for audit fields and validation framework.
    """
    
    # Core fields
    item = models.ForeignKey(
        ItemSKU, 
        on_delete=models.CASCADE, 
        related_name='images',
        help_text="The item this image belongs to"
    )
    image = models.ImageField(
        upload_to=upload_item_image_path,
        help_text="Image file for the item"
    )
    caption = models.CharField(
        max_length=255, 
        blank=True, 
        default='',
        help_text="Optional caption for the image"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as primary image for the item"
    )

    class Meta:
        db_table = 'catalog_itemimage'
        verbose_name = 'Item Image'
        verbose_name_plural = 'Item Images'
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            # will manual check when saving cause it validate on form then invalid
            # models.UniqueConstraint(
            #     fields=['item'],
            #     condition=models.Q(is_primary=True),
            #     name='unique_primary_image_per_item'
            # )
        ]

    def __str__(self):
        primary_text = " (Primary)" if self.is_primary else ""
        caption_text = f" - {self.caption}" if self.caption else ""
        return f"{self.item.sku_code} Image{caption_text}{primary_text}"

    def get_validators(self):
        """Return list of validators for this image"""
        return [
            ItemImageValidator(self),
            ItemImagePrimaryValidator(self),
            ItemImageBusinessRulesValidator(self)
        ]

    def save(self, *args, **kwargs):
        """Save with validation and field normalization"""
        if self.caption:
            self.caption = self.caption.strip()
        # with transaction.atomic():
        if self.is_primary:
            qs = self.__class__.objects.filter(item=self.item, is_primary=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_primary=False)
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete with business rule validation"""        
        # Store info before deletion
        was_primary = self.is_primary
        item = self.item
        
        # Call parent delete first
        super().delete(*args, **kwargs)
        
        # If this was primary image, set another image as primary if available
        if was_primary:
            other_image = ItemImage.objects.filter(item=item).first()
            if other_image:
                # Use update to avoid triggering validation
                ItemImage.objects.filter(pk=other_image.pk).update(is_primary=True)
                
        # Delete the physical file
        from django.core.files.storage import default_storage
        if self.image and default_storage.exists(self.image.name):
            default_storage.delete(self.image.name)

    @property
    def image_url(self):
        """Get the URL of the image file"""
        if self.image:
            return self.image.url
        return None

    @property
    def image_name(self):
        """Get the name of the image file"""
        if self.image:
            return self.image.name.split('/')[-1]
        return None

    @property
    def file_size(self):
        """Get file size in bytes"""
        try:
            return self.image.size if self.image else 0
        except (ValueError, OSError):
            return 0

    @property
    def file_extension(self):
        """Get file extension"""
        if self.image and self.image.name:
            return os.path.splitext(self.image.name)[1].lower()
        return None

    @classmethod
    def get_primary_for_item(cls, item):
        """Get primary image for a specific item, or first image if no primary exists"""
        try:
            return cls.objects.get(item=item, is_primary=True)
        except cls.DoesNotExist:
            # Return first image if no primary exists
            return cls.objects.filter(item=item).first()

    @classmethod
    def set_primary_image(cls, item, image_id):
        """Set a specific image as primary for an item"""
        # First, unset all primary images for the item
        cls.objects.filter(item=item, is_primary=True).update(is_primary=False)

        # Then set the specified image as primary
        try:
            image = cls.objects.get(id=image_id, item=item)
            image.is_primary = True
            image.save()
            return image
        except cls.DoesNotExist:
            return None

    def get_display_name(self):
        """Get formatted display name"""
        caption_part = f" - {self.caption}" if self.caption else ""
        primary_part = " (Primary)" if self.is_primary else ""
        return f"{self.item.sku_code} Image{caption_part}{primary_part}"
