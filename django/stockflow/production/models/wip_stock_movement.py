"""
WIPStockMovement Model

Model สำหรับบันทึกการเคลื่อนไหวของวัสดุใน WIP (Work In Progress) ของแต่ละ Production Order
ใช้แนวทางเดียวกับ ProductionOrder model และรองรับ audit, validation, status
"""

from django.db import models
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin

class WIPStockMovement(AuditableMixin, ValidatableMixin, models.Model):
    """
    WIPStockMovement model สำหรับ track การรับเข้า/เบิกออก/คืน/สูญเสีย/ปรับยอด วัสดุใน WIP ของ production order
    """
    class MovementType(models.TextChoices):
        IN = 'IN', 'IN (รับเข้า WIP)'
        OUT = 'OUT', 'OUT (ใช้ใน process)'
        RETURN = 'RETURN', 'RETURN (คืนจาก WIP)'
        LOSS = 'LOSS', 'LOSS (สูญเสียใน WIP)'
        ADJUST = 'ADJUST', 'ADJUST (ปรับยอด WIP)'

    production_order = models.ForeignKey(
        'production.ProductionOrder',
        on_delete=models.CASCADE,
        related_name='wip_stock_movements',
        help_text="Production order ที่เกี่ยวข้องกับ WIP movement นี้"
    )
    source_stock_movement = models.ForeignKey(
        'inventory.StockMovement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wip_stock_movements',
        help_text="StockMovement ต้นทาง (ถ้ามี เช่น รับเข้า WIP จาก stock จริง)"
    )
    movement_type = models.CharField(
        max_length=10,
        choices=MovementType.choices,
        help_text="ประเภทการเคลื่อนไหวของ WIP"
    )
    item_sku = models.ForeignKey(
        'catalog.ItemSKU',
        on_delete=models.PROTECT,
        related_name='wip_stock_movements',
        help_text="SKU ของวัสดุที่เคลื่อนไหวใน WIP"
    )
    quantity = models.DecimalField(
        max_digits=18, decimal_places=6,
        help_text="จำนวนวัสดุที่เคลื่อนไหว"
    )
    note = models.TextField(blank=True, default='', help_text="หมายเหตุเพิ่มเติม")

    class Meta:
        db_table = 'wip_stock_movement'
        ordering = ['-created_at']
        verbose_name = 'WIP Stock Movement'
        verbose_name_plural = 'WIP Stock Movements'
        indexes = [
            models.Index(fields=['production_order']),
            models.Index(fields=['item_sku']),
            models.Index(fields=['movement_type']),
        ]

    def __str__(self):
        return f"WIPStockMovement({self.production_order_id}, {self.item_sku_id}, {self.movement_type}, {self.quantity})"

    def get_validators(self):
        # สามารถเพิ่ม custom validator ได้ที่นี่
        return []

    @classmethod
    def get_wip_balance(cls, production_order, item_sku):
        """
        คำนวณยอดคงเหลือของ item_sku ใน WIP ของ production_order
        
        Args:
            production_order: ProductionOrder instance
            item_sku: ItemSKU instance
            
        Returns:
            Decimal: ยอดคงเหลือในปัจจุบัน (บวก = มีของในสต็อก, ลบ = ใช้เกิน)
        """
        from django.db.models import Sum, Case, When, DecimalField
        from decimal import Decimal
        
        # คำนวณยอดรวม IN (เข้า) และ OUT/LOSS/ADJUST (ออก)
        movements = cls.objects.filter(
            production_order=production_order,
            item_sku=item_sku
        )
        
        # Debug: Check if there are any movements
        if not movements.exists():
            return Decimal('0')
        
        result = movements.aggregate(
            in_quantity=Sum(
                Case(
                    When(movement_type__in=[cls.MovementType.IN], 
                         then='quantity'),
                    default=0,
                    output_field=DecimalField(max_digits=18, decimal_places=6)
                )
            ),
            out_quantity=Sum(
                Case(
                    When(movement_type__in=[cls.MovementType.OUT, cls.MovementType.LOSS, cls.MovementType.RETURN], 
                         then='quantity'),
                    default=0,
                    output_field=DecimalField(max_digits=18, decimal_places=6)
                )
            )
        )
        
        in_qty = result['in_quantity'] or Decimal('0')
        out_qty = result['out_quantity'] or Decimal('0')
        
        return in_qty - out_qty

    @classmethod
    def get_all_wip_balances(cls, production_order):
        """
        คำนวณยอดคงเหลือของ item_sku ทั้งหมดใน WIP ของ production_order
        
        Args:
            production_order: ProductionOrder instance
            
        Returns:
            dict: {item_sku_id: balance} สำหรับทุก item ที่มี movement
        """
        from django.db.models import Sum, Case, When, DecimalField
        from decimal import Decimal
        
        movements = cls.objects.filter(production_order=production_order)
        
        if not movements.exists():
            return {}
            
        # Group by item_sku and calculate balance for each
        balances = {}
        item_skus = movements.values('item_sku').distinct()
        
        for item_data in item_skus:
            item_sku_id = item_data['item_sku']
            
            # Get movements for this specific item_sku
            item_movements = movements.filter(item_sku_id=item_sku_id)
            
            result = item_movements.aggregate(
                in_quantity=Sum(
                    Case(
                        When(movement_type__in=[cls.MovementType.IN], 
                             then='quantity'),
                        default=0,
                        output_field=DecimalField(max_digits=18, decimal_places=6)
                    )
                ),
                out_quantity=Sum(
                    Case(
                        When(movement_type__in=[cls.MovementType.OUT, cls.MovementType.LOSS, cls.MovementType.RETURN], 
                             then='quantity'),
                        default=0,
                        output_field=DecimalField(max_digits=18, decimal_places=6)
                    )
                )
            )
            
            in_qty = result['in_quantity'] or Decimal('0')
            out_qty = result['out_quantity'] or Decimal('0')
            balance = in_qty - out_qty
            
            if balance != 0:  # Only include non-zero balances
                balances[item_sku_id] = balance
                
        return balances
