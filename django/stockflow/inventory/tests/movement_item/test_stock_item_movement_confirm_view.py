"""
Test Stock Movement Confirm View

Tests for confirming stock movements including permissions, business rules,
error handling, and proper response handling.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied, ValidationError
from unittest.mock import patch

from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse


class StockMovementConfirmViewTest(TestCase):
    """Test case for Stock Movement confirm view"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.unauthorized_user = User.objects.create_user(
            username='unauthorizeduser',
            password='testpass123'
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TW001',
            address='123 Test St, Test City, Test State 12345',
            note='Test warehouse for confirm view testing',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create draft stock movement
        self.draft_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            note='Test draft movement',
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create completed stock movement
        self.completed_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            note='Test completed movement',
            status=StockMovement.Status.COMPLETED,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add permissions to user
        change_permission = Permission.objects.get(codename='change_stockmovement')
        self.user.user_permissions.add(change_permission)
        
        # URL for confirm view
        self.confirm_url = reverse('inventory:stock-movement-confirm', kwargs={'pk': self.draft_movement.pk})
        self.confirm_url_completed = reverse('inventory:stock-movement-confirm', kwargs={'pk': self.completed_movement.pk})

    def test_redirect_if_not_logged_in(self):
        """Test redirect to login if not authenticated"""
        response = self.client.post(self.confirm_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_only_post_method_allowed(self):
        """Test that only POST method is allowed"""
        self.client.login(username='testuser', password='testpass123')
        
        # GET should not be allowed
        response = self.client.get(self.confirm_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # PUT should not be allowed
        response = self.client.put(self.confirm_url)
        self.assertEqual(response.status_code, 405)
        
        # DELETE should not be allowed
        response = self.client.delete(self.confirm_url)
        self.assertEqual(response.status_code, 405)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_successful_confirm_draft_movement(self, mock_check_permission):
        """Test successful confirmation of draft stock movement"""
        mock_check_permission.return_value = True
        
        # Mock the can_be_confirmed method to return True since we don't have items in test
        with patch.object(StockMovement, 'can_be_confirmed', return_value=(True, "")):
            self.client.login(username='testuser', password='testpass123')
            
            # Test HTMX request
            response = self.client.post(self.confirm_url, HTTP_HX_REQUEST='true')
            
            # Debug: Print response content if there's an error
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.content.decode()}")
            
            # Should return 200 with HX-Redirect header for HTMX requests
            self.assertEqual(response.status_code, 200)
            expected_url = reverse('inventory:stock-movement-detail', kwargs={'pk': self.draft_movement.pk})
            self.assertEqual(response['HX-Redirect'], expected_url)
            
            # Check that status was updated
            self.draft_movement.refresh_from_db()
            self.assertEqual(self.draft_movement.status, StockMovement.Status.COMPLETED)
            self.assertEqual(self.draft_movement.updated_by, self.user)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_successful_confirm_non_htmx_request(self, mock_check_permission):
        """Test successful confirmation with non-HTMX request (regular redirect)"""
        mock_check_permission.return_value = True
        
        # Mock the can_be_confirmed method to return True since we don't have items in test
        with patch.object(StockMovement, 'can_be_confirmed', return_value=(True, "")):
            self.client.login(username='testuser', password='testpass123')
            
            # Test regular (non-HTMX) request
            response = self.client.post(self.confirm_url)
            
            # Should redirect to detail page for non-HTMX requests
            self.assertEqual(response.status_code, 302)
            expected_url = reverse('inventory:stock-movement-detail', kwargs={'pk': self.draft_movement.pk})
            self.assertRedirects(response, expected_url)
            
            # Check that status was updated
            self.draft_movement.refresh_from_db()
            self.assertEqual(self.draft_movement.status, StockMovement.Status.COMPLETED)
            self.assertEqual(self.draft_movement.updated_by, self.user)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_confirm_already_completed_movement(self, mock_check_permission):
        """Test confirming already completed movement returns error"""
        mock_check_permission.return_value = True
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.confirm_url_completed)
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
        self.assertIn('Stock movement is already completed', response.content.decode())

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_permission_denied_no_warehouse_access(self, mock_check_permission):
        """Test permission denied when user has no warehouse access"""
        mock_check_permission.return_value = False
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.confirm_url)
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        self.assertIn('permission', response.content.decode().lower())

    def test_permission_denied_no_change_permission(self):
        """Test permission denied when user has no change permission"""
        # Remove change permission
        change_permission = Permission.objects.get(codename='change_stockmovement')
        self.user.user_permissions.remove(change_permission)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.confirm_url)
        
        # Should return 403 Forbidden (handled by WarehousePermissionMixin)
        self.assertEqual(response.status_code, 403)

    def test_404_nonexistent_stock_movement(self):
        """Test 404 error for non-existent stock movement"""
        nonexistent_url = reverse('inventory:stock-movement-confirm', kwargs={'pk': 99999})
        
        # Login with proper permissions
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(nonexistent_url)
        
        # Debug: show what we got instead of 404
        if response.status_code != 404:
            print(f"Expected 404, got {response.status_code}")
            print(f"Response content: {response.content.decode()}")
        
        self.assertEqual(response.status_code, 404)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_error_handling_during_save(self, mock_check_permission):
        """Test error handling when confirm operation fails"""
        mock_check_permission.return_value = True
        
        # Mock the confirm method to raise an exception
        with patch.object(StockMovement, 'confirm', side_effect=Exception("Database error")):
            self.client.login(username='testuser', password='testpass123')
            response = self.client.post(self.confirm_url)
            
            # Should return 500 Internal Server Error
            self.assertEqual(response.status_code, 500)
            self.assertIn('Error confirming', response.content.decode())

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_validation_error_during_confirm(self, mock_check_permission):
        """Test handling of validation errors during confirm"""
        mock_check_permission.return_value = True
        
        # Mock the confirm method to raise a ValidationError
        with patch.object(StockMovement, 'confirm', side_effect=ValidationError("Cannot confirm movement without items")):
            self.client.login(username='testuser', password='testpass123')
            response = self.client.post(self.confirm_url)
            
            # Should return 400 Bad Request for validation error
            self.assertEqual(response.status_code, 400)
            self.assertIn('Validation error', response.content.decode())
            self.assertIn('Cannot confirm movement without items', response.content.decode())

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_updated_by_field_set_correctly(self, mock_check_permission):
        """Test that updated_by field is set to current user"""
        mock_check_permission.return_value = True
        
        # Create another user to confirm the movement
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        change_permission = Permission.objects.get(codename='change_stockmovement')
        other_user.user_permissions.add(change_permission)
        
        with patch.object(StockMovement, 'can_be_confirmed', return_value=(True, "")):
            # Login as other user and confirm
            self.client.login(username='otheruser', password='testpass123')
            response = self.client.post(self.confirm_url, HTTP_HX_REQUEST='true')
            
            # Check that updated_by is set to the other user
            self.draft_movement.refresh_from_db()
            self.assertEqual(self.draft_movement.updated_by, other_user)
            self.assertEqual(self.draft_movement.status, StockMovement.Status.COMPLETED)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_status_unchanged_on_permission_error(self, mock_check_permission):
        """Test that status remains unchanged when permission is denied"""
        mock_check_permission.return_value = False
        
        original_status = self.draft_movement.status
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.confirm_url)
        
        # Status should remain unchanged
        self.draft_movement.refresh_from_db()
        self.assertEqual(self.draft_movement.status, original_status)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_multiple_confirm_attempts_idempotent(self, mock_check_permission):
        """Test that multiple confirm attempts are handled gracefully"""
        mock_check_permission.return_value = True
        
        with patch.object(StockMovement, 'can_be_confirmed', return_value=(True, "")):
            self.client.login(username='testuser', password='testpass123')
            
            # First confirm - should succeed (HTMX request)
            response1 = self.client.post(self.confirm_url, HTTP_HX_REQUEST='true')
            self.assertEqual(response1.status_code, 200)
            self.assertIn('HX-Redirect', response1)
            
            # Second confirm - should return error
            response2 = self.client.post(self.confirm_url, HTTP_HX_REQUEST='true')
            self.assertEqual(response2.status_code, 400)
            self.assertIn('Stock movement is already completed', response2.content.decode())

    def test_unauthorized_user_cannot_confirm(self):
        """Test that unauthorized user cannot confirm movements"""
        self.client.login(username='unauthorizeduser', password='testpass123')
        response = self.client.post(self.confirm_url)
        
        # Should be denied access (403)
        self.assertEqual(response.status_code, 403)
        
        # Status should remain unchanged
        self.draft_movement.refresh_from_db()
        self.assertEqual(self.draft_movement.status, StockMovement.Status.DRAFT)

    @patch('inventory.views.stock_movement_views.StockMovementConfirmView.check_warehouse_permission')
    def test_redirect_url_construction(self, mock_check_permission):
        """Test that redirect URL is constructed correctly"""
        mock_check_permission.return_value = True
        
        with patch.object(StockMovement, 'can_be_confirmed', return_value=(True, "")):
            self.client.login(username='testuser', password='testpass123')
            response = self.client.post(self.confirm_url, HTTP_HX_REQUEST='true')
            
            # Check HX-Redirect header
            expected_url = reverse('inventory:stock-movement-detail', kwargs={'pk': self.draft_movement.pk})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['HX-Redirect'], expected_url)

    def tearDown(self):
        """Clean up after each test"""
        # Clean up is handled automatically by TestCase
        pass
