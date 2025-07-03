from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from catalog.models.category import Category
from simple_history.models import HistoricalRecords

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
    is_bom_locked = models.BooleanField(default=False) # Indicates if the BOM is locked for this item
    version = models.PositiveIntegerField(default=0)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.sku_code} - {self.name}"

    # Validate that the item type cannot be changed once set
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk:  # แปลว่ากำลังอัปเดต ไม่ใช่สร้างใหม่
                      
            old = ItemSKU.objects.get(pk=self.pk)
            # ป้องกันการเปลี่ยนแปลงประเภทของ ItemSKU
            if self.type != old.type:
                raise ValidationError("Item type cannot be changed once set.")
            
            # ป้องกันการเปลี่ยนแปลงประเภทของ sku_code
            if self.sku_code != old.sku_code:
                raise ValidationError("SKU code must be unique and cannot be changed once set.")
            
            # 🔐 ป้องกันการเปลี่ยน is_bom_locked จาก True กลับเป็น False
            if old.is_bom_locked and not self.is_bom_locked:
                raise ValidationError("Cannot unlock a BOM once it has been locked.")
                       
            # Optimistic Locking
            current = ItemSKU.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValidationError("Optimistic Locking failed. The record has changed.")
            self.version += 1
            
        else:
            # เมื่อสร้างใหม่ ให้ตั้งค่า is_bom_locked เป็น True สำหรับประเภท RAW
            if self.type == ItemSKUType.RAW:
                self.is_bom_locked = True
            else:
                self.is_bom_locked = False
        super().save(*args, **kwargs)
