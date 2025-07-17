from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False, null=False)
    note = models.TextField(blank=True, default='')  # Optional note field
    is_active = models.BooleanField(default=True)  # Added active/inactive status
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='categories_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='categories_updated')
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=0)
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['name']
        db_table = 'catalog_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def clean_name(self):
        """Clean and validate name field"""
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty.")
        self.name = self.name.strip()
        
        # Check for duplicate name
        existing_qs = Category.objects.filter(name=self.name)
        if self.pk:
            existing_qs = existing_qs.exclude(pk=self.pk)
        
        if existing_qs.exists():
            raise ValueError(f"Category with name '{self.name}' already exists.")
        
    def save(self, *args, **kwargs):
        # Business logic validation
        self.clean_name()
        
        # Optimistic locking (business logic)
        if self.pk:
            try:
                current = Category.objects.get(pk=self.pk)
                if current.version != self.version:
                    raise ValueError("Optimistic Locking failed. The record has changed.")
                self.version += 1
            except Category.DoesNotExist:
                raise ValueError("Category no longer exists.")
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active(cls):
        """Get all active categories"""
        return cls.objects.filter(is_active=True)
    
    def deactivate(self):
        """Deactivate this category"""
        self.is_active = False
        self.save()
    
    def activate(self):
        """Activate this category"""
        self.is_active = True
        self.save()

    def __str__(self):
        return self.name
