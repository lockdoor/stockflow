from django.db import models
from catalog.models.item import ItemSKU
from inventory.models.warehouse import Warehouse
from common.mixins.auditable import AuditableMixin
from common.mixins.validatable import ValidatableMixin
# from inventory.validators import MaterialReservationValidator

from catalog.models.bom import BOM 
from decimal import Decimal, ROUND_HALF_UP

class MaterialReservation(AuditableMixin, ValidatableMixin, models.Model):
    """
    MaterialReservation status usage:
    - RESERVED: จองวัสดุไว้ (reserved_quantity > 0)
    - COMMITTED: มีการเบิกวัสดุครบตามที่จองไว้ (reserved_quantity = 0 จากการเบิกจริง)
    - RELEASED: คืนจอง/ยกเลิกจอง (reserved_quantity = 0 จากการคืนจอง)
    - CANCELLED: การจองถูกยกเลิก (reserved_quantity = 0) production_order จาก created -> draft

    หมายเหตุ: reserved_quantity ควรเป็น 0 เสมอเมื่อ status เป็น COMMITTED, RELEASED หรือ CANCELLED
    """
    class ReferenceType(models.TextChoices):
        PRODUCTION = 'PRODUCTION', 'Production Order'
        SALES = 'SALES', 'Sales Order'
        # เพิ่ม context อื่น ๆ ได้ตามต้องการ

    class Status(models.TextChoices):
        RESERVED = 'RESERVED', 'Reserved'
        RELEASED = 'RELEASED', 'Released'
        COMMITTED = 'COMMITTED', 'Committed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    reference_type = models.CharField(
        max_length=30,
        choices=ReferenceType.choices,
        help_text="Context ของการจอง เช่น PRODUCTION, SALES"
    )
    reference_id = models.PositiveIntegerField(
        help_text="ID ของ reference เช่น production_order_id, sales_order_id"
    )
    item_sku = models.ForeignKey(
        ItemSKU,
        on_delete=models.PROTECT,
        related_name='material_reservations',
        help_text="Item SKU ที่จอง"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='material_reservations',
        help_text="คลังที่จองวัสดุ"
    )
    reserved_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="จำนวนที่จอง"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RESERVED,
        help_text="สถานะการจอง"
    )

    class Meta:
        db_table = 'inventory_material_reservation'
        verbose_name = 'Material Reservation'
        verbose_name_plural = 'Material Reservations'
        indexes = [
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['item_sku']),
            models.Index(fields=['warehouse']),
        ]
        unique_together = ('reference_type', 'reference_id', 'item_sku', 'warehouse')

    def __str__(self):
        return f"Reservation({self.reference_type}-{self.reference_id}) {self.item_sku} {self.reserved_quantity} @ {self.warehouse}"

    def get_validators(self):
        # Return a list of validators for this model instance
        # use the MaterialReservationValidator(self) if needed
        return [
            # MaterialReservationValidator(self)
        ]
    
       
    @classmethod
    def create_reservation(cls, reference_type, reference_id, item_sku: ItemSKU, warehouse, reserved_quantity, user):
        """
        Create a new material reservation.
        """
        
        if reserved_quantity <= 0:
            raise ValueError("Reserved quantity must be positive.")

        if item_sku.type in [ItemSKU.Type.PRODUCT, ItemSKU.Type.PACKAGE]:
            # For PRODUCT or PACKAGE, we need to reserve for each component in its BOM
            boms = BOM.objects.filter(parent_sku=item_sku)
            if not boms.exists():
                raise ValueError(f"No active BOM found for item SKU {item_sku}. Cannot create reservation.")
            
            # For each component in the BOM
            for bom in boms:
                qty = Decimal(bom.quantity) * Decimal(reserved_quantity)
                qty = qty.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                reservation = cls(
                    reference_type=reference_type,
                    reference_id=reference_id,
                    item_sku=bom.component_sku,
                    warehouse=warehouse,
                    reserved_quantity=qty,
                    created_by=user,
                    updated_by=user
                )
                reservation.full_clean()
                reservation.save()
        else:
            reservation = cls(
                reference_type=reference_type,
                reference_id=reference_id,
                item_sku=item_sku,
                warehouse=warehouse,
                reserved_quantity=reserved_quantity,
                created_by=user,
                updated_by=user
            )
            reservation.full_clean()
            reservation.save()

    @classmethod
    def get_all_product_reservation(cls, product_order):
        """
        Get all material reservations for this instance.
        """
        return cls.objects.filter(
            reference_type=cls.ReferenceType.PRODUCTION,
            reference_id=product_order.id
        )

    @classmethod
    def __repr_with_product_order__(cls, production_order) -> None:
        reservations = cls.objects.filter(
            reference_type=cls.ReferenceType.PRODUCTION,
            reference_id=production_order.id
        )
        print("reservation count: ", reservations.count())
        for reservation in reservations:
            print(reservation)

    def decrease_quantity(self, quantity, user):
        """
        Decrease the reserved quantity.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        if self.reserved_quantity - quantity < 0:
            self.reserved_quantity = 0
        else:
            self.reserved_quantity -= quantity

        if self.reserved_quantity == 0:
            self.status = self.Status.COMMITTED

        self.updated_by = user
        self.save()
