from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from catalog.models.category import Category

class ItemSKUType(models.TextChoices):
    RAW = 'RAW', 'Raw Material'
    PRODUCT = 'PRODUCT', 'Finished Product'
    PACKAGE = 'PACKAGE', 'Package'

class ItemSKUStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'

class ItemSKU(models.Model):
    sku_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    type = models.CharField(
        max_length=20,
        choices=ItemSKUType.choices,
        default=ItemSKUType.RAW,
    )
    status = models.CharField(
        max_length=20,
        choices=ItemSKUStatus.choices,
        default=ItemSKUStatus.ACTIVE,
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='items_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='items_updated')
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')

    def __str__(self):
        return f"{self.sku_code} - {self.name}"

    # Validate that the item type cannot be changed once set
    def save(self, *args, **kwargs):
        if self.pk:  # แปลว่ากำลังอัปเดต ไม่ใช่สร้างใหม่
            old = ItemSKU.objects.get(pk=self.pk)
            if self.type != old.type:
                raise ValidationError("Item type cannot be changed once set.")
        super().save(*args, **kwargs)
