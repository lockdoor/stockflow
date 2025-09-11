from django.db import models

class ProductionStatusMixin(models.Model):
    """
    Mixin to add production status fields and methods to a model.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'  # Initial state
        CREATED = 'CREATED', 'Created'  # After creation
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'  # During production tracking by start time
        PAUSED = 'PAUSED', 'Paused'  # Production paused
        COMPLETED = 'COMPLETED', 'Completed'  # Finished production tracking by finished time
        CANCELLED = 'CANCELLED', 'Cancelled'  # Production halted - WIP materials need to be returned
        CLOSED_COMPLETED = 'CLOSED_COMPLETED', 'Closed (Completed)'  # Production successfully completed and closed
        CLOSED_CANCELLED = 'CLOSED_CANCELLED', 'Closed (Cancelled)'  # Production cancelled and all WIP materials returned

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status of the production order"
    )

    class Meta:
        abstract = True

    def can_cancel(self):
        """Check if production order can be cancelled"""
        return self.status in [
            self.Status.DRAFT,
            self.Status.CREATED,
            self.Status.IN_PROGRESS,
            self.Status.PAUSED
        ]

    def can_close(self):
        """Check if production order can be closed (after materials returned)"""
        return self.status in [
            self.Status.CANCELLED,
            self.Status.COMPLETED
        ]

    def is_active(self):
        """Check if production order is in active status (can have stock movements)"""
        return self.status in [
            self.Status.DRAFT,
            self.Status.CREATED,
            self.Status.IN_PROGRESS,
            self.Status.PAUSED
        ]

    def is_finished(self):
        """Check if production order is finished (no more actions allowed)"""
        return self.status in [
            self.Status.CLOSED_COMPLETED,
            self.Status.CLOSED_CANCELLED
        ]

    def was_completed_successfully(self):
        """Check if production order was closed after successful completion"""
        return self.status == self.Status.CLOSED_COMPLETED

    def was_cancelled(self):
        """Check if production order was cancelled (including closed cancelled)"""
        return self.status in [
            self.Status.CANCELLED,
            self.Status.CLOSED_CANCELLED
        ]

    def can_return_wip_materials(self):
        """Check if production order can have WIP materials returned"""
        return self.status == self.Status.CANCELLED

    def get_status_display_with_context(self):
        """Get status display with additional context about closure reason"""
        if self.status == self.Status.CLOSED_COMPLETED:
            return "Closed (Successfully Completed)"
        elif self.status == self.Status.CLOSED_CANCELLED:
            return "Closed (Cancelled - Materials Returned)"
        else:
            return self.get_status_display()

    def has_wip_materials(self):
        """Check if production order has materials in WIP stock that need to be returned"""
        if not hasattr(self, 'id'):
            return False
            
        from production.models import WIPStockMovement
        
        # Get all WIP balances for this production order
        wip_balances = WIPStockMovement.get_all_wip_balances(self)
        
        # Check if there are any positive balances (materials in WIP)
        for balance in wip_balances.values():
            if balance > 0:
                return True
        
        return False

    def close_as_completed(self, user=None):
        """Close production order as successfully completed"""
        if not self.can_close() or self.status != self.Status.COMPLETED:
            raise ValueError(f"Cannot close production order as completed. Current status: {self.status}")
        
        self.status = self.Status.CLOSED_COMPLETED
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
        self.save()

    def close_as_cancelled(self, user=None):
        """Close production order as cancelled (after materials returned)"""
        if not self.can_close() or self.status != self.Status.CANCELLED:
            raise ValueError(f"Cannot close production order as cancelled. Current status: {self.status}")
        
        # Verify no WIP materials remaining
        if self.has_wip_materials():
            raise ValueError("Cannot close cancelled production order - WIP materials still exist")
        
        self.status = self.Status.CLOSED_CANCELLED
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
        self.save()

    def cancel_production(self, user=None):
        """Cancel production order"""
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel production order. Current status: {self.status}")
        
        self.status = self.Status.CANCELLED
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
        self.save()

    def get_wip_materials_summary(self):
        """Get summary of WIP materials that need to be returned"""
        if not hasattr(self, 'id'):
            return []
            
        from production.models import WIPStockMovement
        from catalog.models import ItemSKU
        
        # Get all WIP balances for this production order
        wip_balances = WIPStockMovement.get_all_wip_balances(self)
        
        materials_summary = []
        for item_sku_id, balance in wip_balances.items():
            if balance > 0:  # Only include positive balances (materials in WIP)
                item_sku = ItemSKU.objects.get(id=item_sku_id)
                materials_summary.append({
                    'item_sku': item_sku,
                    'warehouse': self.warehouse,  # Production order's warehouse
                    'balance': balance
                })
        
        return materials_summary
