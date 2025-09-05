"""
ProductionLoss Model

Model สำหรับบันทึกการสูญเสียในกระบวนการผลิต
"""

from django.db import models
from django.core.exceptions import ValidationError
from common.mixins.auditable import AuditableMixin


class ProductionLoss(AuditableMixin, models.Model):
    """
    Model สำหรับบันทึกการสูญเสียในกระบวนการผลิต
    """
    
    production_process = models.ForeignKey(
        'production.ProductionProcess',
        on_delete=models.CASCADE,
        related_name='production_losses',
        help_text="กระบวนการผลิตที่เกิดการสูญเสีย"
    )
    
    item_sku = models.ForeignKey(
        'catalog.ItemSKU',
        on_delete=models.PROTECT,
        help_text="วัตถุดิบที่สูญเสีย"
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="จำนวนที่สูญเสีย"
    )
    
    reason = models.TextField(
        blank=True,
        help_text="สาเหตุการสูญเสีย"
    )

    class Meta:
        db_table = 'production_loss'
        verbose_name = 'Production Loss'
        verbose_name_plural = 'Production Losses'
        
    def __str__(self):
        return f"Loss: {self.item_sku} - {self.quantity} units"
    
    def clean(self):
        """Validation logic"""
        super().clean()
        
        # ตรวจสอบว่า quantity > 0
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than 0'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
