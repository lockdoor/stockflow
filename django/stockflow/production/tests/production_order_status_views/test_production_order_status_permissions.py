"""
Tests for production order status views permissions
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from production.models import ProductionOrder, ProductionOrderBOM
from catalog.models import BOM, ItemSKU
from inventory.models import Warehouse
from tests.factories.catalog import ItemFactory, ProductFactory
from tests.factories.inventory.warehouse_factory import WarehouseFactory
from tests.factories.production.production_order_factory import ProductionOrderFactory


class ProductionOrderStatusPermissionTestCase(TestCase):
    """Test permissions for production order status views"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user_with_perms = User.objects.create_user(
            username='user_with_perms',
            password='testpass123'
        )
        
        self.user_without_perms = User.objects.create_user(
            username='user_without_perms', 
            password='testpass123'
        )
        
        # Create production order content type and permissions
        production_content_type = ContentType.objects.get_for_model(ProductionOrder)
        self.view_permission = Permission.objects.get(
            codename='view_productionorder',
            content_type=production_content_type
        )
        self.change_permission = Permission.objects.get(
            codename='change_productionorder',
            content_type=production_content_type
        )
        
        # Grant permissions to user_with_perms
        self.user_with_perms.user_permissions.add(
            self.view_permission,
            self.change_permission
        )
        
        # Create test data
        self.item_sku = ItemFactory()
        self.warehouse = WarehouseFactory()
        
        # Create test production orders
        self.draft_order = ProductionOrderFactory(warehouse=self.warehouse)
        
        # Create orders with created status
        self.created_order = ProductionOrderFactory(warehouse=self.warehouse)
        product = ItemSKU.objects.create(
            sku_code="TEST-PROD-001",
            name="Test Product 001",
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            unit="pcs",
            created_by=self.user_with_perms,
            updated_by=self.user_with_perms
        )
        for _ in range(2):
            BOM.objects.create(
                parent_sku=product,
                component_sku=ItemFactory(created_by=self.user_with_perms),
                quantity=10,
                created_by=self.user_with_perms,
                updated_by=self.user_with_perms
            )
        product.status = ItemSKU.Status.ACTIVE
        product.save()
        product.refresh_from_db()
        ProductionOrderBOM.objects.create(
            production_order=self.created_order,
            item_sku=product,
            planned_quantity=10,
            created_by=self.user_with_perms,
            updated_by=self.user_with_perms,
        )
        self.created_order.created_production_order(user=self.user_with_perms)
        # self.created_order.refresh_from_db()
        
        # Create orders with different statuses by using raw SQL to bypass validation
        self.in_progress_order = ProductionOrderFactory(warehouse=self.warehouse)
        ProductionOrder.objects.filter(id=self.in_progress_order.id).update(
            status=ProductionOrder.Status.IN_PROGRESS
        )
        self.in_progress_order.refresh_from_db()
        
        self.cancelled_order = ProductionOrderFactory(warehouse=self.warehouse)
        ProductionOrder.objects.filter(id=self.cancelled_order.id).update(
            status=ProductionOrder.Status.CANCELLED
        )
        self.cancelled_order.refresh_from_db()

    def test_cancel_confirm_view_requires_change_permission(self):
        """Test that cancel confirm view requires change permission"""
        url = reverse('production:production-order-cancel-confirm', kwargs={'pk': self.draft_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # User with permissions should access the view
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancel Production Order')

    def test_cancel_view_requires_change_permission(self):
        """Test that cancel view requires change permission"""
        url = reverse('production:production-order-cancel', kwargs={'pk': self.created_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.post(url, {'confirm_cancel': 'on'})
        self.assertEqual(response.status_code, 403)
        
        # Set status to CREATED to allow cancellation
        self.assertEqual(self.created_order.status, ProductionOrder.Status.CREATED)
        
        # User with permissions should be able to cancel
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.post(url, {'confirm_cancel': 'on'})
        self.assertEqual(response.status_code, 302)  # Redirect after successful cancel
        
        # Verify the order was cancelled
        self.created_order.refresh_from_db()
        self.assertEqual(self.created_order.status, ProductionOrder.Status.CANCELLED)

    def test_return_wip_view_requires_change_permission(self):
        """Test that return WIP view requires change permission"""
        url = reverse('production:production-order-return-wip', kwargs={'pk': self.cancelled_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # User with permissions should access the view
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Return WIP Materials')

    def test_close_completed_view_requires_change_permission(self):
        """Test that close completed view requires change permission"""
        url = reverse('production:production-order-close-completed', kwargs={'pk': self.in_progress_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        
        # User with permissions should be able to close
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful close
        
        # Verify the order was closed as completed
        # self.in_progress_order.refresh_from_db()
        # self.assertEqual(self.in_progress_order.status, ProductionOrder.Status.CLOSED_COMPLETED)

    def test_close_cancelled_view_requires_change_permission(self):
        """Test that close cancelled view requires change permission"""
        url = reverse('production:production-order-close-cancelled', kwargs={'pk': self.cancelled_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        
        # User with permissions should be able to close
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful close
        
        # Verify the order was closed as cancelled
        self.cancelled_order.refresh_from_db()
        self.assertEqual(self.cancelled_order.status, ProductionOrder.Status.CLOSED_CANCELLED)

    def test_status_api_requires_view_permission(self):
        """Test that status API requires view permission"""
        url = reverse('production:production-order-status-api', kwargs={'pk': self.draft_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # User with view permission should access the API
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check API response data
        data = response.json()
        self.assertEqual(data['id'], self.draft_order.id)
        self.assertEqual(data['status'], self.draft_order.status)
        self.assertIn('status_display', data)
        self.assertIn('can_cancel', data)

    def test_nonexistent_production_order_returns_404(self):
        """Test that accessing non-existent production order returns 404"""
        nonexistent_pk = 99999
        
        self.client.login(username='user_with_perms', password='testpass123')
        
        # Test all views with non-existent pk
        urls = [
            reverse('production:production-order-cancel-confirm', kwargs={'pk': nonexistent_pk}),
            reverse('production:production-order-cancel', kwargs={'pk': nonexistent_pk}),
            reverse('production:production-order-return-wip', kwargs={'pk': nonexistent_pk}),
            reverse('production:production-order-close-completed', kwargs={'pk': nonexistent_pk}),
            reverse('production:production-order-close-cancelled', kwargs={'pk': nonexistent_pk}),
            reverse('production:production-order-status-api', kwargs={'pk': nonexistent_pk}),
        ]
        
        for url in urls:
            with self.subTest(url=url):
                if 'api' in url:
                    response = self.client.get(url)
                elif 'cancel-confirm' in url or 'return-wip' in url:
                    response = self.client.get(url)
                else:
                    response = self.client.post(url)

                self.assertIn(response.status_code, [404, 400])

    def test_user_with_only_view_permission_cannot_modify(self):
        """Test that user with only view permission cannot modify production orders"""
        # Create user with only view permission
        view_only_user = User.objects.create_user(
            username='view_only_user',
            password='testpass123'
        )
        view_only_user.user_permissions.add(self.view_permission)
        
        self.client.login(username='view_only_user', password='testpass123')
        
        # Should be able to access status API
        api_url = reverse('production:production-order-status-api', kwargs={'pk': self.draft_order.pk})
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        
        # Should not be able to access modification views
        modify_urls = [
            reverse('production:production-order-cancel-confirm', kwargs={'pk': self.draft_order.pk}),
            reverse('production:production-order-cancel', kwargs={'pk': self.draft_order.pk}),
            reverse('production:production-order-return-wip', kwargs={'pk': self.cancelled_order.pk}),
            reverse('production:production-order-close-completed', kwargs={'pk': self.in_progress_order.pk}),
            reverse('production:production-order-close-cancelled', kwargs={'pk': self.cancelled_order.pk}),
        ]
        
        for url in modify_urls:
            with self.subTest(url=url):
                if 'cancel-confirm' in url or 'return-wip' in url:
                    response = self.client.get(url)
                else:
                    response = self.client.post(url)
                
                self.assertEqual(response.status_code, 403)

    def test_bulk_return_wip_materials_post(self):
        """Test POST method for bulk return WIP materials"""
        url = reverse('production:production-order-return-wip', kwargs={'pk': self.cancelled_order.pk})
        
        # User without permissions should be denied
        self.client.login(username='user_without_perms', password='testpass123')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        
        # User with permissions should be able to perform bulk return
        self.client.login(username='user_with_perms', password='testpass123')
        response = self.client.post(url)
        
        # Should redirect after successful operation (even if no WIP materials)
        self.assertEqual(response.status_code, 302)
        
        # Verify redirect location
        expected_redirect = reverse('production:production-order-detail', kwargs={'pk': self.cancelled_order.pk})
        self.assertRedirects(response, expected_redirect)

    def test_anonymous_user_blocked(self):
        """Test that anonymous users are blocked from accessing protected views"""
        urls = [
            reverse('production:production-order-cancel-confirm', kwargs={'pk': self.draft_order.pk}),
            reverse('production:production-order-cancel', kwargs={'pk': self.draft_order.pk}),
            reverse('production:production-order-return-wip', kwargs={'pk': self.cancelled_order.pk}),
            reverse('production:production-order-close-completed', kwargs={'pk': self.in_progress_order.pk}),
            reverse('production:production-order-close-cancelled', kwargs={'pk': self.cancelled_order.pk}),
            reverse('production:production-order-status-api', kwargs={'pk': self.draft_order.pk}),
        ]
        
        for url in urls:
            with self.subTest(url=url):
                if 'cancel-confirm' in url or 'return-wip' in url or 'api' in url:
                    response = self.client.get(url)
                else:
                    response = self.client.post(url)
                
                # Anonymous users should be blocked (403 Forbidden or 302 redirect)
                self.assertIn(response.status_code, [302, 403])
