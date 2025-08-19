
"""
ProductionOrder Model

This module defines the ProductionOrder model using mixins for audit, status, and validation.
Follows the same pattern as Category model.
"""

from django.db import models
from common.mixins.auditable import AuditableMixin
from common.mixins.status import StatusMixin
from common.mixins.validatable import ValidatableMixin

class ProductionOrder(AuditableMixin, StatusMixin, ValidatableMixin, models.Model):
    """
    ProductionOrder model for production management.
    Represents a production order with status, warehouse, and audit trail.
    """
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),  # Initial state
        ("CREATED", "Created"),  # After creation
        ("IN_PROGRESS", "In Progress"),  # During production tracking by start time
        ("PAUSED", "Paused"),  # Production paused
        ("COMPLETED", "Completed"),  # Finished production tracking by finished time
        ("CANCELLED", "Cancelled"),  # Production halted
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
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

    def __str__(self):
        return f"ProductionOrder #{self.id} ({self.get_status_display()})"

    def get_validators(self):
        # สามารถเพิ่ม custom validator ได้ที่นี่
        return []

    def save(self, *args, **kwargs):
        # สามารถเพิ่ม business rule validation ได้ที่นี่
        self.full_clean()
        super().save(*args, **kwargs)
