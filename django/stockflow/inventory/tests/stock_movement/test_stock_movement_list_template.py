"""
Test file for checking the updated stock-movement-list template pattern
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement


class StockMovementListTemplateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
    def test_stock_movement_list_loads(self):
        """Test that stock movement list view loads successfully"""
        self.client.login(username='testuser', password='testpass')
        
        url = reverse('inventory:stock-movement-list', args=[self.warehouse.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Movements - Test Warehouse')
        self.assertContains(response, 'Add New DRAFT')
        
    def test_stock_movement_list_with_movements(self):
        """Test stock movement list with existing movements"""
        # Create a stock movement
        movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.NONE,
            note='Test movement',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass')
        
        url = reverse('inventory:stock-movement-list', args=[self.warehouse.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test movement')
        self.assertContains(response, movement.pk)
        
    def test_stock_movement_list_empty(self):
        """Test stock movement list when empty"""
        self.client.login(username='testuser', password='testpass')
        
        url = reverse('inventory:stock-movement-list', args=[self.warehouse.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No stock movements found for this warehouse')
