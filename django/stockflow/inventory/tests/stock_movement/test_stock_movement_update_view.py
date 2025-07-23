from inventory.signals import warehouse_signals
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
from django.urls import reverse

class StockMovementUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Main', 
            code='MAIN01',  # Added required code field
            address='123 Main St',
            note='Main warehouse for testing',
            created_by=self.user, 
            updated_by=self.user)
        self.movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            reference_type=StockMovement.ReferenceType.NONE,
            reference_id=None,  # Should be None when reference_type is NONE
            note='original',
            created_by=self.user,
            updated_by=self.user
        )
        self.update_url = reverse('inventory:stock-movement-edit', args=[self.movement.id])
        # สร้าง permission ทั้งสองแบบ
        self.perm1 = Permission.objects.get(codename='change_stockmovement')
        self.perm2 = Permission.objects.get(codename=f'can_manage_warehouse_{self.warehouse.id}')
       
    def test_update_with_change_stockmovement_permission(self):
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,
            'reference_id': 99,
            'note': 'updated1',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, 'updated1')
        self.assertEqual(self.movement.reference_id, 99)

    def test_update_with_can_manage_warehouse_permission(self):
        self.user.user_permissions.add(self.perm2)
        self.client.login(username='testuser', password='testpass')
        data = {
            'reference_type': StockMovement.ReferenceType.PACKING_LIST,  # Changed from NONE
            'reference_id': 100,  # Now valid since reference_type is not NONE
            'note': 'updated2',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, 'updated2')
        self.assertEqual(self.movement.reference_id, 100)

    def test_update_without_permission(self):
        self.client.login(username='testuser', password='testpass')
        
        # Store original note to verify it doesn't change
        original_note = self.movement.note
        
        data = {
            'reference_type': StockMovement.ReferenceType.ADJUST,
            'reference_id': 101,
            'note': 'should not update',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 403)
        
        # Refresh and verify data wasn't updated
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, original_note)  # Should still be 'original'

    def test_get_update_form_with_permission(self):
        """Test that GET request returns the form correctly"""
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'original')  # Should contain current note value

    def test_get_update_form_without_permission(self):
        """Test that GET request is denied without permission"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

    def test_update_sets_updated_by_field(self):
        """Test that update sets the updated_by field correctly"""
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        
        # Create a different user to verify updated_by change
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.movement.updated_by = other_user
        self.movement.save()
        
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            # reference_id omitted when reference_type is NONE
            'note': 'updated by test',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.updated_by, self.user)
        self.assertEqual(self.movement.note, 'updated by test')

    def test_update_form_invalid_data(self):
        """Test that invalid form data is handled correctly"""
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        
        # Missing required fields
        data = {
            'note': 'incomplete data',
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        
        # Check that HX headers are set correctly for form errors
        self.assertEqual(response.get('HX-Retarget'), '#stock-movement-form')
        self.assertEqual(response.get('HX-Reswap'), 'innerHTML')
        
        # Verify the movement wasn't updated
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, 'original')

    def test_update_response_contains_correct_headers(self):
        """Test that successful update returns correct HTMX headers"""
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            # reference_id omitted when reference_type is NONE
            'note': 'updated successfully',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        
        # Check that success trigger is set
        self.assertEqual(response.get('HX-Trigger'), 'success')
        
        # Verify the movement was updated
        self.movement.refresh_from_db()
        self.assertEqual(self.movement.note, 'updated successfully')

    def test_update_nonexistent_movement(self):
        """Test that updating non-existent movement returns 404"""
        self.user.user_permissions.add(self.perm1)
        self.client.login(username='testuser', password='testpass')
        
        nonexistent_url = reverse('inventory:stock-movement-edit', args=[999999])
        data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            # reference_id omitted when reference_type is NONE
            'note': 'should not work',
            'warehouse': self.warehouse.id,
            'status': StockMovement.Status.DRAFT,
        }
        response = self.client.post(nonexistent_url, data)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_redirected(self):
        """Test that unauthenticated user is redirected to login"""
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)