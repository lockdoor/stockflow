from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='warehouses_created')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='warehouses_updated')
    version = models.PositiveIntegerField(default=1)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Optimistic Locking
        if self.pk:
            current = Warehouse.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValidationError("Optimistic Locking failed. The record has changed.")
            self.version += 1
        super().save(*args, **kwargs)
