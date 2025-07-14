from django.db import models
from inventory.models.stock_movement import StockMovement
from catalog.models.item import ItemSKU
from simple_history.models import HistoricalRecords

class StockMovementItem(models.Model):
    class MovementType(models.TextChoices):
        IN_ = 'IN', 'IN'
        OUT = 'OUT', 'OUT'

    stock_movement = models.ForeignKey(StockMovement, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(ItemSKU, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=3, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    lot = models.CharField(max_length=64, blank=True, null=True)
    expired = models.DateField(blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1, editable=False)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('stock_movement', 'item', 'lot', 'movement_type')
        verbose_name = 'Stock Movement Item'
        verbose_name_plural = 'Stock Movement Items'

    def __str__(self):
        return f"{self.item} {self.movement_type} x {self.quantity} (Movement {self.stock_movement_id})"
    
    def save(self, *args, **kwargs):
        if self.pk:
            current = StockMovementItem.objects.get(pk=self.pk)
            if current.stock_movement.status == StockMovement.Status.CONFIRMED:
                raise ValueError("Cannot modify confirmed stock movement items.")
            if current.version != self.version:
                raise ValueError("Optimistic locking failed. The record has changed.")
            self.version += 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.stock_movement.status == StockMovement.Status.CONFIRMED:
            raise ValueError("Cannot delete item from confirmed stock movement.")
        super().delete(*args, **kwargs)