
"""
ProductionOrder Model

This module defines the ProductionOrder model using mixins for audit, status, and validation.
Follows the same pattern as Category model.
"""

from django.db import models, transaction
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin
from production.mixins.production_status import ProductionStatusMixin
from production.validators import (
    ProductionOrderInitialStatusValidator, 
    ProductionOrderStatusDraftToCreatedValidator,
    ProductionOrderCanNotChangeWareHouseValidator
)

class ProductionOrder(AuditableMixin, ProductionStatusMixin, ValidatableMixin, models.Model):
    """
    ProductionOrder model for production management.
    Represents a production order with status, warehouse, and audit trail.
    """

    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.PROTECT,
        related_name='production_orders',
        help_text="Warehouse for this production order"
    )
    note = models.TextField(blank=True, default='', help_text="Optional notes")
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'production_order'
        ordering = ['-created_at']
        verbose_name = 'Production Order'
        verbose_name_plural = 'Production Orders'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['warehouse']),
        ]
        
    def save(self):
        self.full_clean()
        super().save()
        
    def delete(self, *args, **kwargs):
        
        # Only DRAFT production orders can be deleted.
        if self.status != self.Status.DRAFT:
            from django.core.exceptions import ValidationError
            raise ValidationError("Only DRAFT production orders can be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"ProductionOrder #{self.id} ({self.get_status_display()})"
    
    def __repr__(self):
        text = self.__str__()
        products = self.boms.all()
        for product in products:
            text += f"\n  - {product}"
        return text

    def get_validators(self):
        # สามารถเพิ่ม custom validator ได้ที่นี่
        return [
            ProductionOrderInitialStatusValidator(self),
            ProductionOrderStatusDraftToCreatedValidator(self),
            ProductionOrderCanNotChangeWareHouseValidator(self),
        ]

    def save(self, *args, **kwargs):
        # สามารถเพิ่ม business rule validation ได้ที่นี่
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def bom_count(self) -> int:
        from django.db.models import Count
        obj = self.__class__.objects.filter(id=self.pk).annotate(num_boms=Count("boms")).first()
        return obj.num_boms
    
    def created_production_order(self, user):
        """
        Change status from DRAFT to CREATED. And reserve material.
        """
        with transaction.atomic():
            prev_status = self.__class__.objects.get(id=self.id).status
            if prev_status != self.Status.DRAFT:
                raise ValueError("Can only change status from DRAFT to CREATED.")
            self.status = self.Status.CREATED
            self.updated_by = user
            
            # Reserve material
            from inventory.models.material_reservation import MaterialReservation
            # products = self.get_all_products()
            products = self.boms.all()
            if products.count() == 0:
                raise ValueError("Cannot create production order. No BOM items found.")
            for product in products:
                MaterialReservation.create_reservation(
                    reference_type=MaterialReservation.ReferenceType.PRODUCTION,
                    reference_id=self.id,
                    item_sku=product.item_sku,
                    warehouse=self.warehouse,
                    reserved_quantity=product.planned_quantity,
                    user=user
                )
            
            self.save()
       
    def draft_production_order(self, user):
        """
        Change status from CREATED to DRAFT. Delete all material reservations for this order.
        """

        with transaction.atomic():
            prev_status = self.__class__.objects.get(id=self.id).status
            if prev_status != self.Status.CREATED:
                raise ValueError("Can only change status from CREATED to DRAFT.")

            # Delete all reservations for this production order
            self.get_all_reservations().delete()

            self.status = self.Status.DRAFT
            self.updated_by = user
            self.save()
       
    def get_all_reservations(self):
        from inventory.models import MaterialReservation
        return MaterialReservation.objects.filter(
            reference_type=MaterialReservation.ReferenceType.PRODUCTION,
            reference_id=self.id
        )

    def get_bom_material_items(self):
        """
        Get all material items required for this production order based on BOM
        """
        return self.boms.all()
