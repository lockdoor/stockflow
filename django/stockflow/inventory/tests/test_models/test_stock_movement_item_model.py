from django.test import TestCase
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from catalog.models.item import ItemSKU
from inventory.models.warehouse import Warehouse
from django.contrib.auth.models import User
from datetime import date

class StockMovementItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='test')
        self.warehouse = Warehouse.objects.create(
            name='Main', address='123', note='test', 
            created_by=self.user, updated_by=self.user
        )
        self.item = ItemSKU.objects.create(
            name='Test Item', sku_code='SKU001', 
            unit='pcs', created_by=self.user, updated_by=self.user)
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_stock_movement_item(self):
        item = StockMovementItem.objects.create(
            stock_movement=self.movement,
            item_sku=self.item,
            movement_type=StockMovementItem.MovementType.IN,
            quantity=10,
            note='test',
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.stock_movement, self.movement)
        self.assertEqual(item.item, self.item)
        self.assertEqual(item.movement_type, 'IN')
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.lot, 'A1')
        self.assertEqual(item.expired, date(2025, 12, 31))
        self.assertEqual(item.note, 'test')

    # def test_unique_together_constraint(self):
    #     StockMovementItem.objects.create(
    #         stock_movement=self.movement,
    #         item=self.item,
    #         movement_type=StockMovementItem.MovementType.IN,
    #         quantity=5,
    #         lot='A1',
    #     )
    #     with self.assertRaises(Exception):
    #         StockMovementItem.objects.create(
    #             stock_movement=self.movement,
    #             item=self.item,
    #             movement_type=StockMovementItem.MovementType.IN,
    #             quantity=7,
    #             lot='A1',
    #         )

    # def test_str_method(self):
    #     item = StockMovementItem.objects.create(
    #         stock_movement=self.movement,
    #         item=self.item,
    #         movement_type=StockMovementItem.MovementType.OUT,
    #         quantity=2,
    #     )
    #     self.assertIn('Test Item', str(item))
    #     self.assertIn('OUT', str(item))
    #     self.assertIn('2', str(item))
    #     self.assertIn(str(self.movement.id), str(item))

    # def test_optimistic_locking(self):
    #     item = StockMovementItem.objects.create(
    #         stock_movement=self.movement,
    #         item=self.item,
    #         movement_type=StockMovementItem.MovementType.IN,
    #         quantity=1,
    #     )
    #     item_copy = StockMovementItem.objects.get(pk=item.pk)
    #     item.quantity = 2
    #     item.save()
    #     item_copy.quantity = 3
    #     with self.assertRaises(ValueError):
    #         item_copy.save()

    # def test_prevent_modify_if_confirmed(self):
    #     item = StockMovementItem.objects.create(
    #         stock_movement=self.movement,
    #         item=self.item,
    #         movement_type=StockMovementItem.MovementType.IN,
    #         quantity=1,
    #     )
    #     self.movement.status = StockMovement.Status.CONFIRMED
    #     self.movement.save()
    #     item.quantity = 5
    #     with self.assertRaises(ValueError):
    #         item.save()

    # def test_prevent_delete_if_confirmed(self):
    #     item = StockMovementItem.objects.create(
    #         stock_movement=self.movement,
    #         item=self.item,
    #         movement_type=StockMovementItem.MovementType.IN,
    #         quantity=1,
    #     )
    #     self.movement.status = StockMovement.Status.CONFIRMED
    #     self.movement.save()
    #     with self.assertRaises(ValueError):
    #         item.delete()
