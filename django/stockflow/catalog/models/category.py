from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False, null=False)
    description = models.TextField(blank=True, default='') # Optional description field
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='categories_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='categories_updated')
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=0)
    history = HistoricalRecords()
    
    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError('Name cannot be empty.')
        if self.name.strip() == '':
            raise ValidationError('Name cannot be empty.')
        if len(self.name) > 100:
            raise ValidationError('Name cannot exceed 100 characters.')
        
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk:
            current = Category.objects.get(pk=self.pk)
            if current.version != self.version:
                raise ValidationError("Optimistic Locking failed. The record has changed.")
            self.version += 1
        if self.description is None:
            self.description = ''
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
