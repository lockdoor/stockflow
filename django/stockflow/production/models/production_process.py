"""
ProductionProcess Model

Model สำหรับบันทึกกระบวนการผลิตของแต่ละ Production Order
รองรับการ track การเริ่ม-จบกระบวนการผลิต และเชื่อมโยงกับ ProductionResult และ ProductionLoss
"""

from django.db import models
from django.core.exceptions import ValidationError
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin


class ProductionProcess(AuditableMixin, ValidatableMixin, models.Model):
    """
    ProductionProcess model สำหรับ track กระบวนการผลิตของ production order
    """
    
    class StatusChoices(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
    
    production_order = models.ForeignKey(
        'production.ProductionOrder',
        on_delete=models.CASCADE,
        related_name='production_processes',
        help_text="Production order ที่เกี่ยวข้องกับกระบวนการผลิตนี้"
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        help_text="สถานะของกระบวนการผลิต"
    )
    
    process_name = models.CharField(
        max_length=255,
        help_text="ชื่อกระบวนการผลิต (เช่น 'การตัด', 'การเย็บ', 'การตรวจสอบคุณภาพ')"
    )
    
    started_at = models.DateTimeField(
        null=True, blank=True,
        help_text="วันเวลาที่เริ่มกระบวนการผลิต"
    )
    
    finished_at = models.DateTimeField(
        null=True, blank=True,
        help_text="วันเวลาที่เสร็จสิ้นกระบวนการผลิต"
    )
    
    note = models.TextField(
        blank=True, default='',
        help_text="หมายเหตุเพิ่มเติมเกี่ยวกับกระบวนการผลิต"
    )

    class Meta:
        db_table = 'production_process'
        ordering = ['-created_at']
        verbose_name = 'Production Process'
        verbose_name_plural = 'Production Processes'
        indexes = [
            models.Index(fields=['production_order']),
            models.Index(fields=['started_at']),
            models.Index(fields=['finished_at']),
        ]
        constraints = [
            # Ensure only one draft production process per production order
            models.UniqueConstraint(
                fields=['production_order'],
                condition=models.Q(status='DRAFT'),
                name='unique_draft_per_production_order'
            )
        ]

    def __str__(self):
        return f"ProductionProcess({self.production_order_id}, {self.process_name}, {self.get_status_display()})"

    def clean(self):
        """Validate business rules"""
        super().clean()
        
        # ตรวจสอบว่า finished_at ต้องไม่เร็วกว่า started_at
        if self.started_at and self.finished_at:
            if self.finished_at < self.started_at:
                raise ValidationError({
                    'finished_at': 'Finished time cannot be earlier than started time.'
                })

    def get_validators(self):
        """Return custom validators"""
        return []

    @property
    def is_draft(self):
        """Check if process is in draft status"""
        return self.status == self.StatusChoices.DRAFT

    @property
    def is_confirmed(self):
        """Check if process is confirmed"""
        return self.status == self.StatusChoices.CONFIRMED

    @property
    def is_started(self):
        """Check if process has started"""
        return self.started_at is not None

    @property
    def is_finished(self):
        """Check if process has finished"""
        return self.finished_at is not None

    @property
    def duration(self):
        """Get process duration if both start and finish times are available"""
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None

    def start_process(self, user, start_time=None):
        """Start the production process"""
        from django.utils import timezone
        
        if self.is_started:
            raise ValidationError("Process has already been started.")
            
        self.started_at = start_time or timezone.now()
        self.updated_by = user
        self.save()

    def finish_process(self, user, finish_time=None):
        """Finish the production process"""
        from django.utils import timezone
        
        if not self.is_started:
            raise ValidationError("Process must be started before it can be finished.")
            
        if self.is_finished:
            raise ValidationError("Process has already been finished.")
            
        self.finished_at = finish_time or timezone.now()
        self.updated_by = user
        self.save()

    def confirm_process(self, user):
        """Confirm the production process and update WIP inventory"""
        from django.db import transaction
        from django.utils import timezone
        
        if not self.is_draft:
            raise ValidationError("Only draft processes can be confirmed.")
            
        with transaction.atomic():
            # Update status to confirmed and set finished_at automatically
            self.status = self.StatusChoices.CONFIRMED
            self.finished_at = timezone.now()  # กำหนดเวลาเสร็จสิ้นอัตโนมัติ
            self.updated_by = user
            self.save()
            
            # Apply production results and losses to WIP inventory
            self._apply_results_to_wip(user)
            self._apply_losses_to_wip(user)
            
            return self
    
    def _apply_results_to_wip(self, user):
        """Apply production results to WIP inventory - ตรวจสอบวัตถุดิบและหักการใช้งาน"""
        from production.models.wip_stock_movement import WIPStockMovement
        from catalog.models import BOM
        from django.db.models import Sum
        
        # ตรวจสอบว่ามีวัตถุดิบเพียงพอสำหรับการผลิตหรือไม่
        for result in self.production_results.all():
            # หา BOM ของ product ที่จะผลิต
            bom_materials = BOM.objects.filter(parent_sku=result.item_sku).select_related('component_sku')
            
            if not bom_materials.exists():
                raise ValidationError(
                    f'Cannot produce {result.item_sku.name}: No BOM (Bill of Materials) found. '
                    f'Please define BOM first.'
                )
            
            # ตรวจสอบว่ามีวัตถุดิบเพียงพอในแต่ละ component
            insufficient_materials = []
            for bom in bom_materials:
                required_quantity = bom.quantity * result.quantity  # จำนวนที่ต้องใช้
                available_balance = WIPStockMovement.get_wip_balance(
                    self.production_order, 
                    bom.component_sku
                )
                
                if available_balance < required_quantity:
                    insufficient_materials.append(
                        f'{bom.component_sku.name}: required {required_quantity}, available {available_balance}'
                    )
            
            if insufficient_materials:
                raise ValidationError(
                    f'Insufficient materials in WIP for producing {result.quantity} units of {result.item_sku.name}:\n' +
                    '\n'.join(insufficient_materials)
                )
        
        # หักวัตถุดิบที่ใช้ในการผลิต
        for result in self.production_results.all():
            bom_materials = BOM.objects.filter(parent_sku=result.item_sku).select_related('component_sku')
            
            # หักวัตถุดิบสำหรับแต่ละ component
            for bom in bom_materials:
                used_quantity = bom.quantity * result.quantity
                
                # สร้าง OUT movement สำหรับวัตถุดิบที่ใช้
                WIPStockMovement.objects.create(
                    production_order=self.production_order,
                    item_sku=bom.component_sku,
                    movement_type='OUT',
                    quantity=used_quantity,
                    note=f'Used in production of {result.quantity} {result.item_sku.name} - Process: {self.process_name}',
                    created_by=user,
                    updated_by=user
                )
            
            # เพิ่ม finished product เข้า WIP
            WIPStockMovement.objects.create(
                production_order=self.production_order,
                item_sku=result.item_sku,
                movement_type='IN',
                quantity=result.quantity,
                note=f'Production result from process: {self.process_name} - {result.note}',
                created_by=user,
                updated_by=user
            )
    
    def _apply_losses_to_wip(self, user):
        """Apply production losses to WIP inventory (decrease stock)"""
        from production.models.wip_stock_movement import WIPStockMovement
        
        for loss in self.production_losses.all():
            # สร้าง WIP stock movement สำหรับ production loss (ลด stock)
            WIPStockMovement.objects.create(
                production_order=self.production_order,
                item_sku=loss.item,
                movement_type='LOSS',
                quantity=loss.quantity,
                note=f'Production loss from process: {self.process_name} - {loss.get_loss_reason_display()} - {loss.note}',
                created_by=user,
                updated_by=user
            )

    def delete(self, *args, **kwargs):
        """Override delete to only allow deletion of draft processes"""
        if not self.is_draft:
            raise ValidationError("Only draft processes can be deleted.")
        return super().delete(*args, **kwargs)
