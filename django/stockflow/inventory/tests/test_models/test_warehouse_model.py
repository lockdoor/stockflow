from django.test import TestCase
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse
from django.core.exceptions import ValidationError

class WarehouseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')

    def test_create_warehouse_success(self):
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            address='123 Main St',
            note='Central storage',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(warehouse.name, 'Main Warehouse')
        self.assertEqual(warehouse.address, '123 Main St')
        self.assertTrue(warehouse.is_active)
        self.assertEqual(warehouse.created_by, self.user)
        self.assertEqual(warehouse.updated_by, self.user)

    def test_str_method(self):
        warehouse = Warehouse.objects.create(
            name='Secondary',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(str(warehouse), 'Secondary')

    def test_inactive_warehouse(self):
        warehouse = Warehouse.objects.create(
            name='Inactive',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        self.assertFalse(warehouse.is_active)
        
    def test_optimistic_locking(self):
        warehouse = Warehouse.objects.create(
            name='Optimistic Lock',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(warehouse.version, 1)
        
        copy_warehouse = Warehouse.objects.get(pk=warehouse.pk)
        
        self.assertEqual(copy_warehouse.version, 1)
        
        # Simulate an update
        warehouse.name = 'Updated Name'
        warehouse.save()
        self.assertEqual(warehouse.version, 2)
        self.assertEqual(copy_warehouse.version, 1)
        
        # Test optimistic locking failure
        with self.assertRaises(ValidationError):
            copy_warehouse.name = 'Another Update'
            copy_warehouse.save()
