from django.db import models
from django.contrib.auth.models import User
from .warehouse import Warehouse
from simple_history.models import HistoricalRecords

class StockMovement(models.Model):
    class ReferenceType(models.TextChoices):
        NONE = 'NONE', 'None'
        ADJUST = 'ADJUST', 'Adjust'
        PACKING_LIST = 'PACKING_LIST', 'Packing List'
        PRODUCTION = 'PRODUCTION', 'Production'
        INVOICE = 'INVOICE', 'Invoice'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        CONFIRMED = 'CONFIRMED', 'Confirmed'

    reference_type = models.CharField(
        max_length=20,
        choices=ReferenceType.choices,
        default=ReferenceType.NONE
    )
    reference_id = models.IntegerField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='stock_movements_created')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='stock_movements_updated')
    history = HistoricalRecords()
    version = models.PositiveIntegerField(default=1, editable=False)

    class Meta:
        constraints = [
            # this constraint ensures that there is only one draft stock movement per warehouse
            models.UniqueConstraint(
                fields=['warehouse'],
                condition=models.Q(status='DRAFT'),
                name='unique_draft_per_warehouse'
            )
        ]

    def __str__(self):
        return f"Stock movement id: #{self.id} ({self.status}) on warehouse: {self.warehouse.name})"
    
    def save(self, *args, **kwargs):
        # DRAFT: สามารถสร้าง/แก้ไข/ลบได้
        # CONFIRMED: immutable
        if self.pk:
            current = StockMovement.objects.get(pk=self.pk)
            if current.status == StockMovement.Status.CONFIRMED:
                raise ValueError("Confirmed StockMovement instances cannot be updated.")
            if self.status == StockMovement.Status.CONFIRMED:
                # เมื่อยืนยัน ให้เปลี่ยนเป็น immutable
                pass  # สามารถเพิ่ม business logic เช่น trigger อัปเดต StockBalance ที่นี่
            # Optimistic Locking
            if current.version != self.version:
                raise ValueError("Optimistic Locking failed. The record has changed.")
            self.version += 1
            
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == StockMovement.Status.CONFIRMED:
            raise ValueError("Confirmed StockMovement instances cannot be deleted.")
        super().delete(*args, **kwargs)
