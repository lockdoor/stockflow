from django.db import models
from catalog.models.item import ItemSKU, ItemSKUType
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

class BOM(models.Model):
    parent_sku = models.ForeignKey(ItemSKU, on_delete=models.CASCADE, related_name='bom_parent')
    component_sku = models.ForeignKey(ItemSKU, on_delete=models.PROTECT, related_name='bom_component')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    version = models.PositiveIntegerField(default=0)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.parent_sku.sku_code} needs {self.quantity} x {self.component_sku.sku_code}"

    def save(self, *args, **kwargs):
        if self.parent_sku.type == ItemSKUType.RAW:
            raise ValidationError("Cannot create BOM with parent SKU as a raw material.")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.parent_sku == self.component_sku:
            raise ValidationError("Parent SKU and component SKU cannot be the same.")
        
        # ห้ามเพิ่ม component ซ้ำ
        if not self.pk and BOM.objects.filter(parent_sku=self.parent_sku, component_sku=self.component_sku).exists():
            raise ValidationError("This component already exists in the BOM.")
        
        if self.pk:
            if self.parent_sku.is_bom_locked:
                raise ValidationError("BOM cannot be updated if locked.")
            
            # Optimistic Locking
            current = BOM.objects.get(pk=self.pk)
            if self.version != current.version:
                raise ValidationError("Optimistic Locking failed: BOM record has changed.")
            self.version += 1

        super().save(*args, **kwargs)
