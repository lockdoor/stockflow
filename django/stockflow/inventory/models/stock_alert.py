"""
Stock Alert Model

This module defines the StockAlert model for managing stock threshold alerts.
Uses AuditableMixin for audit fields and optimistic locking,
and ValidatableMixin for validation.

Author: StockFlow Team
Created: 2025
"""

from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin
from catalog.models import ItemSKU
from .warehouse import Warehouse


class StockAlert(AuditableMixin, ValidatableMixin, models.Model):
    """
    Stock Alert model for managing stock threshold notifications.
    
    Represents alert configurations for specific item-warehouse combinations.
    Supports minimum and critical thresholds with enable/disable functionality.
    """
    
    # Core relationships
    item_sku = models.ForeignKey(
        ItemSKU,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        help_text="The item SKU for this alert"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        help_text="The warehouse for this alert"
    )
    
    # Threshold fields
    minimum_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Minimum stock level that triggers a warning alert"
    )
    critical_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Critical stock level that triggers an urgent alert"
    )
    
    # Configuration
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this alert is active"
    )
    note = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this alert configuration"
    )
    
    class Meta:
        db_table = 'inventory_stock_alert'
        verbose_name = 'Stock Alert'
        verbose_name_plural = 'Stock Alerts'
        unique_together = ['item_sku', 'warehouse']
        indexes = [
            models.Index(fields=['item_sku'], name='idx_stock_alert_item'),
            models.Index(fields=['warehouse'], name='idx_stock_alert_warehouse'),
            models.Index(fields=['is_enabled'], name='idx_stock_alert_enabled'),
        ]
    
    def __str__(self):
        return f"Alert: {self.item_sku.sku_code} @ {self.warehouse.code} (Min: {self.minimum_threshold})"
    
    def clean(self):
        """
        Validate the stock alert data.
        """
        super().clean()
        
        # Validate that critical threshold is less than or equal to minimum threshold
        if self.critical_threshold and self.minimum_threshold:
            if self.critical_threshold > self.minimum_threshold:
                raise ValidationError({
                    'critical_threshold': 'Critical threshold must be less than or equal to minimum threshold.'
                })
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def alert_levels(self):
        """
        Return a dictionary of alert levels for easy access.
        """
        return {
            'minimum': self.minimum_threshold,
            'critical': self.critical_threshold
        }
    
    def is_stock_below_minimum(self, current_stock):
        """
        Check if current stock is below minimum threshold.
        
        Args:
            current_stock (Decimal): Current stock quantity
            
        Returns:
            bool: True if stock is below minimum threshold
        """
        if not self.is_enabled:
            return False
        return current_stock <= self.minimum_threshold
    
    def is_stock_critical(self, current_stock):
        """
        Check if current stock is at critical level.
        
        Args:
            current_stock (Decimal): Current stock quantity
            
        Returns:
            bool: True if stock is at critical level
        """
        if not self.is_enabled:
            return False
        return current_stock <= self.critical_threshold
    
    @property
    def current_stock(self):
        """
        Get current total stock for this item in this warehouse.
        
        Returns:
            Decimal: Total available quantity in this warehouse
        """
        from inventory.models import Stock
        total = Stock.objects.filter(
            item_sku=self.item_sku,
            warehouse=self.warehouse,
            available_quantity__gt=0
        ).aggregate(
            total=models.Sum('available_quantity')
        )['total']
        return total or 0
    
    def get_alert_level(self, current_stock=None):
        """
        Get the current alert level based on stock quantity.
        
        Args:
            current_stock (Decimal, optional): Current stock quantity. 
                                             If None, will calculate from database
            
        Returns:
            str: 'critical', 'warning', or 'normal'
        """
        if not self.is_enabled:
            return 'normal'
        
        if current_stock is None:
            current_stock = self.current_stock
            
        if self.is_stock_critical(current_stock):
            return 'critical'
        elif self.is_stock_below_minimum(current_stock):
            return 'warning'  # เปลี่ยนจาก 'minimum' เป็น 'warning' ให้ตรงกับ template
        else:
            return 'normal'
