from django.test import TestCase
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement, StockMovementReferenceType, StockMovementStatus

class StockMovementModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            address='123 Main St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_draft_stock_movement_success(self):
        movement = StockMovement.objects.create(
            reference_type=StockMovementReferenceType.PACKING_LIST,
            reference_id=123,
            note='Receive goods',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user,
            status=StockMovementStatus.DRAFT
        )
        self.assertEqual(movement.status, StockMovementStatus.DRAFT)
        self.assertEqual(movement.reference_type, StockMovementReferenceType.PACKING_LIST)
        self.assertEqual(movement.reference_id, 123)
        self.assertEqual(movement.note, 'Receive goods')
        self.assertEqual(movement.warehouse, self.warehouse)
        self.assertEqual(movement.created_by, self.user)

    def test_update_draft_stock_movement(self):
        movement = StockMovement.objects.create(
            reference_type=StockMovementReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user,
            status=StockMovementStatus.DRAFT
        )
        movement.note = 'Update draft note'
        movement.save()
        movement.refresh_from_db()
        self.assertEqual(movement.note, 'Update draft note')

    def test_confirmed_stock_movement_is_immutable(self):
        movement = StockMovement.objects.create(
            reference_type=StockMovementReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user,
            status=StockMovementStatus.DRAFT
        )
        # Confirm movement
        movement.status = StockMovementStatus.CONFIRMED
        movement.save()
        # Try to update after confirmed
        movement.note = 'Try to update after confirm'
        with self.assertRaises(ValueError) as e:
            movement.save()
        self.assertEqual(str(e.exception), "Confirmed StockMovement instances cannot be updated.")

    def test_confirmed_stock_movement_cannot_be_deleted(self):
        movement = StockMovement.objects.create(
            reference_type=StockMovementReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user,
            status=StockMovementStatus.CONFIRMED
        )
        with self.assertRaises(ValueError) as e:
            movement.delete()
        self.assertEqual(str(e.exception), "Confirmed StockMovement instances cannot be deleted.")

    def test_unique_draft_per_warehouse(self):
        StockMovement.objects.create(
            reference_type=StockMovementReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user,
            status=StockMovementStatus.DRAFT
        )
        with self.assertRaises(Exception):
            StockMovement.objects.create(
                reference_type=StockMovementReferenceType.PACKING_LIST,
                warehouse=self.warehouse,
                created_by=self.user,
                status=StockMovementStatus.DRAFT
            )

    # Optimistic Locking
    def test_optimistic_locking_on_draft(self):
        # สมมุติ StockMovement มี field version (integer, default=1, +1 ทุกครั้งที่ save)
        movement = StockMovement.objects.create(
            reference_type=StockMovementReferenceType.ADJUST,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user,
            status=StockMovementStatus.DRAFT
        )
        # ดึง movement สอง instance
        m1 = StockMovement.objects.get(pk=movement.pk)
        m2 = StockMovement.objects.get(pk=movement.pk)
        # m1 update ก่อน
        m1.note = 'First update'
        m1.version = m1.version  # version = 1
        m1.save()
        # m2 พยายาม update ด้วย version เดิม
        m2.note = 'Second update'
        m2.version = m2.version  # version = 1 (เก่า)
        with self.assertRaises(ValueError) as e:
            m2.save()
        self.assertEqual(str(e.exception), "Optimistic Locking failed. The record has changed.")