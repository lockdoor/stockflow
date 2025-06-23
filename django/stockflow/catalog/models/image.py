from django.db import models
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU

class ItemImage(models.Model):
    item = models.ForeignKey('ItemSKU', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item_images/')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='item_images_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='item_images_updated')
    updated_at = models.DateTimeField(auto_now=True)
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item.sku_code} - Image"
