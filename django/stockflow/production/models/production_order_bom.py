
from django.db import models
from production.models.production_order import ProductionOrder
from catalog.models.item import ItemSKU
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin
from production.validators import (
    ProductionOrderBOMUpdateValidator,
    ProductionOrderBOMItemMustBeTypeProduct
)

class ProductionOrderBOM(AuditableMixin, ValidatableMixin, models.Model):
    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.CASCADE,
        related_name='boms',
        help_text="Production order this BOM belongs to"
    )
    item_sku = models.ForeignKey(
        ItemSKU,
        on_delete=models.PROTECT,
        help_text="ItemSKU to be produced by this BOM"
    )
    planned_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Planned quantity to produce"
    )
    note = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'production_order_bom'
        verbose_name = 'Production Order BOM'
        verbose_name_plural = 'Production Order BOMs'
        indexes = [
            models.Index(fields=['production_order']),
            models.Index(fields=['item_sku']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['production_order', 'item_sku'], name='unique_bom_item')
        ]
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"BOM for Order {self.production_order_id} - {self.item_sku} ({self.planned_quantity})"

    def __repr__(self):
        return (
            f"ProductionOrderBOM(order_id={self.production_order_id}, "
            f"item_sku={self.item_sku}, planned_quantity={self.planned_quantity}, "
            f"created_by={self.created_by}, updated_by={self.updated_by}, version={self.version})"
        )

    @property
    def is_active(self) -> bool:
        """Assume BOM is active if its order is not cancelled"""
        return self.production_order.status != self.production_order.Status.CANCELLED

    @property
    def is_editable(self) -> bool:
        """BOM is editable if order is in DRAFT or CREATED status"""
        return self.production_order.status in [
            self.production_order.Status.DRAFT,
            self.production_order.Status.CREATED
        ]

    def get_validators(self):
        """Return list of validators for this BOM (implement as needed)"""
        # from production.validators.product_order_bom_validators import ProductionOrderBOMBusinessRulesValidator
        # return [ProductionOrderBOMBusinessRulesValidator(self)]
        return [
            ProductionOrderBOMUpdateValidator(self),
            ProductionOrderBOMItemMustBeTypeProduct(self)
        ]
