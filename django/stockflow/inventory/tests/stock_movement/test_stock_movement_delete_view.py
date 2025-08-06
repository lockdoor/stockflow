"""
Stock Movement Delete View Tests

Tests for StockMovementDeleteView including permission checking, business rules,
redirect handling, and next URL functionality.

Author: StockFlow Team
Created: 2025
"""

from inventory.signals import warehouse_signals
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
from django.urls import reverse


class StockMovementDeleteViewTest(TestCase):
    """Test cases for StockMovementDeleteView with enhanced next URL functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create test warehouse
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse', 
            code='MAIN01',
            address='123 Main St',
            note='Main warehouse for testing',
            is_active=True,
            created_by=self.user, 
            updated_by=self.user
        )
        
        # Create stock movements for testing
        self.confirmed_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.CONFIRMED,
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=123,
            note='Confirmed movement for testing',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.draft_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            status=StockMovement.Status.DRAFT,
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=456,
            note='Draft movement for testing',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Setup permissions
        self.delete_permission = Permission.objects.get(codename='delete_stockmovement')
        
        # Get warehouse-specific permission (created by signal)
        self.warehouse_permission = Permission.objects.get(
            codename=f'can_manage_warehouse_{self.warehouse.id}'
        )
        
        # URLs for testing
        self.delete_draft_url = reverse('inventory:stock-movement-delete', kwargs={'pk': self.draft_movement.pk})
        self.delete_confirmed_url = reverse('inventory:stock-movement-delete', kwargs={'pk': self.confirmed_movement.pk})

    def test_found_can_manage_warehouse_permission(self):
        """Test that warehouse-specific permission exists"""
        perm_codename = f'can_manage_warehouse_{self.warehouse.id}'
        permission = Permission.objects.get(codename=perm_codename)
        self.assertIsNotNone(permission)
        self.assertEqual(permission.codename, perm_codename)

    def test_delete_requires_authentication(self):
        """Test that delete requires user to be logged in"""
        response = self.client.post(self.delete_draft_url)
        # Should be forbidden without login due to WarehousePermissionMixin
        self.assertEqual(response.status_code, 403)

    def test_delete_draft_with_global_permission(self):
        """Test deletion with global delete permission"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Verify movement exists before deletion
        self.assertTrue(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())
        
        response = self.client.post(self.delete_draft_url)
        
        # Should redirect after successful deletion
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_draft_with_warehouse_permission(self):
        """Test deletion with warehouse-specific permission"""
        # Add warehouse permission (need base delete permission too for mixin to work properly)
        self.user.user_permissions.add(self.delete_permission)
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.delete_draft_url)
        
        # Should redirect after successful deletion
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_without_permission(self):
        """Test deletion fails without proper permissions"""
        # No permissions granted
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(self.delete_draft_url)
        
        # Should be forbidden or redirect with error
        self.assertIn(response.status_code, [302, 403])
        self.assertTrue(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_delete_confirmed_should_fail(self):
        """Test that confirmed movements cannot be deleted"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.delete_confirmed_url)
        
        # Should redirect back to detail page (not delete)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StockMovement.objects.filter(pk=self.confirmed_movement.pk).exists())

    def test_delete_not_found(self):
        """Test deletion of non-existent stock movement"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        nonexistent_url = reverse('inventory:stock-movement-delete', kwargs={'pk': 99999})
        response = self.client.post(nonexistent_url)
        
        self.assertEqual(response.status_code, 404)

    def test_delete_different_warehouse_permission_denied(self):
        """Test that warehouse-specific permission only works for that warehouse"""
        # Create another warehouse and stock movement
        other_warehouse = Warehouse.objects.create(
            name='Other Warehouse',
            code='OTHER01',
            address='456 Other St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        other_movement = StockMovement.objects.create(
            warehouse=other_warehouse,
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Give user permission only for the first warehouse
        self.user.user_permissions.add(self.warehouse_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Should fail to delete movement from other warehouse
        other_delete_url = reverse('inventory:stock-movement-delete', kwargs={'pk': other_movement.pk})
        response = self.client.post(other_delete_url)
        
        self.assertIn(response.status_code, [302, 403])
        self.assertTrue(StockMovement.objects.filter(pk=other_movement.pk).exists())

    # ========================
    # NEW TESTS FOR NEXT URL FUNCTIONALITY
    # ========================
    
    def test_redirect_to_next_url_from_get_parameter(self):
        """Test redirect to next URL provided in GET parameter"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        next_url = '/custom/redirect/path/'
        url_with_next = f"{self.delete_draft_url}?next={next_url}"
        
        response = self.client.post(url_with_next)
        
        # Should redirect to the specified next URL
        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_redirect_to_next_url_from_post_parameter(self):
        """Test redirect to next URL provided in POST data"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        next_url = '/another/custom/path/'
        
        response = self.client.post(self.delete_draft_url, {'next': next_url})
        
        # Should redirect to the specified next URL
        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_redirect_to_warehouse_list_as_fallback(self):
        """Test redirect to general stock movement list when no next URL provided"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.delete_draft_url)
        
        # Should redirect to general stock movement list
        expected_url = reverse('inventory:stock-movement-list')
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_get_parameter_takes_priority_over_post(self):
        """Test that GET parameter takes priority over POST parameter for next URL"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        get_next = '/get/priority/path/'
        post_next = '/post/path/'
        
        url_with_next = f"{self.delete_draft_url}?next={get_next}"
        
        response = self.client.post(url_with_next, {'next': post_next})
        
        # Should redirect to GET parameter URL, not POST
        self.assertRedirects(response, get_next, fetch_redirect_response=False)

    def test_get_success_redirect_url_method(self):
        """Test the get_success_redirect_url method directly"""
        from inventory.views.stock_movement_views import StockMovementDeleteView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        
        view = StockMovementDeleteView()
        view.request = request
        
        # Test with next parameter
        view.request.GET = {'next': '/custom/path/'}
        result = view.get_success_redirect_url(self.draft_movement)
        self.assertEqual(result, '/custom/path/')
        
        # Test without next parameter (should use general list)
        view.request.GET = {}
        view.request.POST = {}
        result = view.get_success_redirect_url(self.draft_movement)
        expected = reverse('inventory:stock-movement-list')
        self.assertEqual(result, expected)

    def test_fallback_to_general_list_on_error(self):
        """Test fallback to general stock movement list if URL generation fails"""
        from inventory.views.stock_movement_views import StockMovementDeleteView
        from django.test import RequestFactory
        from unittest.mock import patch
        
        factory = RequestFactory()
        request = factory.get('/')
        
        view = StockMovementDeleteView()
        view.request = request
        view.request.GET = {}
        view.request.POST = {}
        
        # Mock reverse to raise an exception
        with patch('inventory.views.stock_movement_views.reverse') as mock_reverse:
            mock_reverse.side_effect = Exception("URL error")
            
            result = view.get_success_redirect_url(self.draft_movement)
            # Should fall back to hardcoded URL
            self.assertEqual(result, '/inventory/stockmovement/')

    def test_success_message_displayed(self):
        """Test that success message is set after deletion"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.delete_draft_url, follow=True)
        
        # Check for success message in messages framework
        messages = list(response.context['messages'])
        self.assertTrue(any('deleted successfully' in str(message) for message in messages))

    def test_error_message_for_confirmed_movement(self):
        """Test that error message is shown when trying to delete confirmed movement"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(self.delete_confirmed_url, follow=True)
        
        # Check for error message
        messages = list(response.context['messages'])
        self.assertTrue(any('Cannot delete confirmed' in str(message) for message in messages))

    def test_post_method_delegates_to_delete(self):
        """Test that POST method properly delegates to delete method"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Both POST and DELETE should work the same way
        response = self.client.post(self.delete_draft_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())

    def test_business_rule_validation_timing(self):
        """Test that business rule validation happens before deletion"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Try to delete confirmed movement
        initial_count = StockMovement.objects.count()
        
        response = self.client.post(self.delete_confirmed_url)
        
        # Count should remain the same (no deletion occurred)
        final_count = StockMovement.objects.count()
        self.assertEqual(initial_count, final_count)
        
        # Should redirect back to detail page
        expected_redirect = reverse('inventory:stock-movement-detail', kwargs={'pk': self.confirmed_movement.pk})
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

    def test_url_encoding_in_next_parameter(self):
        """Test that URL encoding in next parameter is handled correctly"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        # URL with encoded characters
        next_url = '/path/with%20spaces/and%3Fquery%3Dvalue'
        url_with_next = f"{self.delete_draft_url}?next={next_url}"
        
        response = self.client.post(url_with_next)
        
        # Should redirect to the URL (Django will handle decoding)
        self.assertEqual(response.status_code, 302)

    def test_multiple_movements_deletion_isolation(self):
        """Test that deleting one movement doesn't affect others"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.login(username='testuser', password='testpass')
        
        # Count movements before deletion
        initial_count = StockMovement.objects.count()
        
        response = self.client.post(self.delete_draft_url)
        
        # Should have one less movement
        final_count = StockMovement.objects.count()
        self.assertEqual(final_count, initial_count - 1)
        
        # Draft movement should be deleted
        self.assertFalse(StockMovement.objects.filter(pk=self.draft_movement.pk).exists())
        # Confirmed movement should still exist
        self.assertTrue(StockMovement.objects.filter(pk=self.confirmed_movement.pk).exists())

    def test_view_class_attributes(self):
        """Test that view has correct class attributes"""
        from inventory.views.stock_movement_views import StockMovementDeleteView
        
        self.assertEqual(StockMovementDeleteView.permission_required_base, 'delete_stockmovement')

    def test_view_inheritance_and_mixins(self):
        """Test that view properly inherits from required mixins"""
        from inventory.views.stock_movement_views import StockMovementDeleteView
        from inventory.mixins.warehouse import WarehousePermissionMixin
        from django.contrib.auth.mixins import LoginRequiredMixin
        from django.views.generic import View
        
        # Check inheritance hierarchy
        self.assertTrue(issubclass(StockMovementDeleteView, WarehousePermissionMixin))
        self.assertTrue(issubclass(StockMovementDeleteView, LoginRequiredMixin))
        self.assertTrue(issubclass(StockMovementDeleteView, View))


