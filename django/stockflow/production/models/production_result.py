"""
ProductionResult Model

Model สำหรับบันทึกผลผลิตที่ได้จากกระบวนการผลิต
"""

from django.db import models
from django.core.exceptions import ValidationError
from common.mixins.auditable import AuditableMixin


class ProductionResult(AuditableMixin, models.Model):
    """
    Model สำหรับบันทึกผลผลิตจาก Production Process
    """
    
    production_process = models.ForeignKey(
        'production.ProductionProcess',
        on_delete=models.CASCADE,
        related_name='production_results',
        help_text="กระบวนการผลิตที่ให้ผลผลิตนี้"
    )
    
    item_sku = models.ForeignKey(
        'catalog.ItemSKU',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="สินค้าที่ผลิตได้"
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="จำนวนที่ผลิตได้"
    )
    
    note = models.TextField(
        blank=True, default='',
        help_text="หมายเหตุเพิ่มเติมเกี่ยวกับกระบวนการผลิต"
    )

    class Meta:
        db_table = 'production_result'
        verbose_name = 'Production Result'
        verbose_name_plural = 'Production Results'
        constraints = [
            models.UniqueConstraint(
                fields=['production_process', 'item_sku'],
                name='unique_production_result_per_process'
            )
        ]
        
    def __str__(self):
        return f"{self.item_sku.name} - {self.quantity} units"
    
    def clean(self):
        """Validation logic"""
        super().clean()
        
        # ตรวจสอบว่า quantity > 0
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than 0'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
