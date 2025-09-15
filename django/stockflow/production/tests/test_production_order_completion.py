"""
Test cases for production order completion feature.

Tests for the new completion functionality where if actual quantity >= planned quantity,
the Cancel button changes to Complete with similar flow including confirm page and WIP material return.
"""

from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model

from production.models import ProductionOrder, ProductionOrderBOM, ProductionResult, ProductionProcess
from inventory.models import StockMovement, StockMovementItem, Stock
from tests.factories.user import AdminFactory
from tests.factories import WarehouseFactory, ProductionOrderFactory
from tests.factories.catalog import ProductFactory
from tests.factories.production import ProductionOrderBOMFactory

User = get_user_model()


class ProductionOrderCompletionModelTests(TestCase):
    """Test the new completion-related model methods"""
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.product1 = ProductFactory(created_by=self.admin_user)
        self.product2 = ProductFactory(created_by=self.admin_user)
        
        # Create production order in DRAFT status first
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create BOMs while in DRAFT status
        self.bom1 = ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=self.product1,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        self.bom2 = ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=self.product2,
            planned_quantity=5,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Now change to IN_PROGRESS status for testing
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.IN_PROGRESS
        )
        self.production_order.refresh_from_db()

    def create_production_result(self, item_sku, quantity):
        """Helper method to create production results with proper process"""
        # Create a production process
        process = ProductionProcess.objects.create(
            production_order=self.production_order,
            status=ProductionProcess.StatusChoices.CONFIRMED,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create production result
        return ProductionResult.objects.create(
            production_process=process,
            item_sku=item_sku,
            quantity=quantity,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

    def test_is_production_complete_with_all_targets_met(self):
        """Test is_production_complete when all actual >= planned"""
        # Create production results that meet all targets
        self.create_production_result(self.product1, 12)  # >= 10 planned
        self.create_production_result(self.product2, 5)   # >= 5 planned
        
        self.assertTrue(self.production_order.is_production_complete())
    
    def test_is_production_complete_with_partial_targets(self):
        """Test is_production_complete when some actual < planned"""
        # Create production results that don't meet all targets
        self.create_production_result(self.product1, 8)   # < 10 planned
        self.create_production_result(self.product2, 5)   # >= 5 planned
        
        self.assertFalse(self.production_order.is_production_complete())
    
    def test_is_production_complete_with_no_actual_production(self):
        """Test is_production_complete with no production results"""
        # No production results created
        self.assertFalse(self.production_order.is_production_complete())
    
    def test_is_production_complete_with_no_boms(self):
        """Test is_production_complete with no BOM items"""
        # Delete all BOMs
        ProductionOrderBOM.objects.filter(production_order=self.production_order).delete()
        
        # Should return True if no BOMs exist (nothing to complete)
        self.assertTrue(self.production_order.is_production_complete())
    
    def test_multiple_production_results_aggregation(self):
        """Test that actual_quantity aggregates multiple production results correctly"""
        # Create multiple production results for the same item
        self.create_production_result(self.product1, 6)
        self.create_production_result(self.product1, 4)
        
        # Total should be 10, which equals planned quantity
        bom = self.production_order.boms.get(item_sku=self.product1)
        self.assertEqual(bom.actual_quantity, 10)
        
    def test_can_complete_production_with_correct_status_and_targets(self):
        """Test can_complete_production with IN_PROGRESS status and targets met"""
        # Create production results that meet targets
        self.create_production_result(self.product1, 10)
        self.create_production_result(self.product2, 5)
        
        self.assertTrue(self.production_order.can_complete_production())
    
    def test_can_complete_production_with_partial_targets(self):
        """Test can_complete_production with IN_PROGRESS status but partial targets"""
        # Create production results that don't meet all targets
        self.create_production_result(self.product1, 8)  # < planned
        
        self.assertFalse(self.production_order.can_complete_production())
    
    def test_can_complete_production_with_wrong_status(self):
        """Test can_complete_production with non-IN_PROGRESS status"""
        # Change status to something other than IN_PROGRESS
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.DRAFT
        )
        self.production_order.refresh_from_db()
        
        self.assertFalse(self.production_order.can_complete_production())


class ProductionOrderCompleteViewTests(TestCase):
    """Test the complete view functionality"""
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.product = ProductFactory(created_by=self.admin_user)
        
        # Create production order with proper flow
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create BOM while in DRAFT status
        self.bom = ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Change to IN_PROGRESS status and add production results
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.IN_PROGRESS
        )
        self.production_order.refresh_from_db()
        
        # Add production results to meet targets
        self.create_production_result(self.product, 10)
        
        self.client.force_login(self.admin_user)

    def create_production_result(self, item_sku, quantity):
        """Helper method to create production results with proper process"""
        # Create a production process
        process = ProductionProcess.objects.create(
            production_order=self.production_order,
            status=ProductionProcess.StatusChoices.CONFIRMED,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create production result
        return ProductionResult.objects.create(
            production_process=process,
            item_sku=item_sku,
            quantity=quantity,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

    def test_complete_confirm_view_get_success(self):
        """Test GET request to complete confirm view"""
        url = reverse('production:production-order-complete-confirm', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url, HTTP_REFERER='/production/orders/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete Production Order Confirmation')
        self.assertContains(response, self.production_order.id)

    def test_complete_confirm_view_access_denied_for_wrong_status(self):
        """Test access denied when production order cannot be completed"""
        # Change to a status that cannot be completed
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.DRAFT
        )
        
        url = reverse('production:production-order-complete-confirm', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url)
        
        # Should redirect due to access denied
        self.assertEqual(response.status_code, 302)

    def test_complete_confirm_view_access_denied_for_partial_production(self):
        """Test access denied when production targets not met"""
        # Delete production results to make targets not met
        ProductionResult.objects.filter(production_process__production_order=self.production_order).delete()
        
        url = reverse('production:production-order-complete-confirm', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url)
        
        # Should redirect due to targets not met
        self.assertEqual(response.status_code, 302)

    def test_complete_view_post_success_without_wip(self):
        """Test successful completion POST without WIP materials"""
        url = reverse('production:production-order-complete', 
                     kwargs={'pk': self.production_order.pk})
        
        response = self.client.post(url, {
            'confirm_complete': True,
            'completion_reason': 'Test completion'
        })
        
        # Should redirect to detail view
        self.assertEqual(response.status_code, 302)
        
        # Refresh the production order from database
        self.production_order.refresh_from_db()
        
        # Check that status was changed to CLOSED_COMPLETED
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_COMPLETED)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('completed successfully' in str(m) for m in messages))

    def test_complete_view_post_missing_confirmation(self):
        """Test POST without confirmation checkbox"""
        url = reverse('production:production-order-complete', 
                     kwargs={'pk': self.production_order.pk})
        
        response = self.client.post(url, {
            'completion_reason': 'Test completion'
            # Missing 'confirm_complete'
        })
        
        # Should redirect back to confirm page
        self.assertEqual(response.status_code, 302)
        self.assertIn('complete/confirm', response.url)

    def test_complete_view_post_unauthorized_user(self):
        """Test POST with unauthorized user"""
        # Create a user without production permissions
        unauthorized_user = User.objects.create_user(
            username='unauthorized',
            password='testpass123'
        )
        
        self.client.force_login(unauthorized_user)
        
        url = reverse('production:production-order-complete', 
                     kwargs={'pk': self.production_order.pk})
        
        response = self.client.post(url, {
            'confirm_complete': True,
            'completion_reason': 'Test completion'
        })
        
        # Should return 403 due to permission denied
        self.assertEqual(response.status_code, 403)


class ProductionOrderCompleteWithWIPTests(TransactionTestCase):
    """Test completion with WIP materials - needs TransactionTestCase for atomic blocks"""
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.product = ProductFactory(created_by=self.admin_user)
        
        # Create production order with proper flow
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create BOM while in DRAFT status
        self.bom = ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Change to IN_PROGRESS status
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.IN_PROGRESS
        )
        self.production_order.refresh_from_db()
        
        # Add production results
        self.create_production_result(self.product, 10)
        
        # Force login the admin user
        self.client.force_login(self.admin_user)

    def create_production_result(self, item_sku, quantity):
        """Helper method to create production results with proper process"""
        # Create a production process
        process = ProductionProcess.objects.create(
            production_order=self.production_order,
            status=ProductionProcess.StatusChoices.CONFIRMED,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create production result
        return ProductionResult.objects.create(
            production_process=process,
            item_sku=item_sku,
            quantity=quantity,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

    def test_complete_confirm_view_shows_wip_materials(self):
        """Test that confirm view shows WIP materials that will be returned"""
        # Create initial stock for the product
        Stock.objects.create(
            warehouse=self.warehouse,
            item_sku=self.product,
            available_quantity=10,
            lot_number='INIT-001',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create a WIP stock movement for this production order
        stock_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=self.production_order.id,
            status=StockMovement.Status.DRAFT,  # Create as DRAFT first
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create stock movement item
        StockMovementItem.objects.create(
            stock_movement=stock_movement,
            item_sku=self.product,
            quantity=5,
            movement_type=StockMovementItem.MovementType.OUT,
            lot_number='WIP-TEST-001',
            note='WIP Material',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Now confirm the stock movement
        stock_movement.confirm(user=self.admin_user)
        
        url = reverse('production:production-order-complete-confirm', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url, HTTP_REFERER='/production/orders/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'WIP Materials to be Returned')
        self.assertContains(response, 'WIP Material')

    def test_complete_view_post_success_with_wip_materials(self):
        """Test successful completion POST with WIP materials return"""
        # Create initial stock for the product
        Stock.objects.create(
            warehouse=self.warehouse,
            item_sku=self.product,
            available_quantity=10,
            lot_number='INIT-002',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create WIP stock movement that will be returned
        stock_movement = StockMovement.objects.create(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=self.production_order.id,
            status=StockMovement.Status.DRAFT,  # Create as DRAFT first
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        StockMovementItem.objects.create(
            stock_movement=stock_movement,
            item_sku=self.product,
            quantity=3,
            movement_type=StockMovementItem.MovementType.OUT,
            lot_number='WIP-TEST-002',
            note='WIP Material',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Now confirm the stock movement
        stock_movement.confirm(user=self.admin_user)
        
        url = reverse('production:production-order-complete', 
                     kwargs={'pk': self.production_order.pk})
        
        response = self.client.post(url, {
            'confirm_complete': True,
            'completion_reason': 'Test completion with WIP return'
        })
        
        # Should redirect to detail view
        self.assertEqual(response.status_code, 302)
        
        # Refresh the production order from database
        self.production_order.refresh_from_db()
        
        # Check that status was changed to CLOSED_COMPLETED
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_COMPLETED)
        
        # Check that a return stock movement was created
        return_movements = StockMovement.objects.filter(
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=self.production_order.id,
        ).exclude(id=stock_movement.id)  # Exclude the original WIP movement
        self.assertTrue(return_movements.exists())


class ProductionOrderDetailViewCompletionTests(TestCase):
    """Test how the detail view shows completion-related buttons and information"""
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.product = ProductFactory(created_by=self.admin_user)
        
        # Create production order and move to COMPLETED status with proper flow
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create BOM while in DRAFT
        self.bom = ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Move to IN_PROGRESS status
        ProductionOrder.objects.filter(id=self.production_order.id).update(
            status=ProductionOrder.Status.IN_PROGRESS
        )
        self.production_order.refresh_from_db()
        
        self.client.force_login(self.admin_user)

    def create_production_result(self, item_sku, quantity):
        """Helper method to create production results with proper process"""
        # Create a production process
        process = ProductionProcess.objects.create(
            production_order=self.production_order,
            status=ProductionProcess.StatusChoices.CONFIRMED,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create production result
        return ProductionResult.objects.create(
            production_process=process,
            item_sku=item_sku,
            quantity=quantity,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )

    def test_detail_view_shows_complete_button_when_targets_met(self):
        """Test detail view shows Complete Order button when production targets are met"""
        # Add production results that meet targets
        self.create_production_result(self.product, 10)
        
        url = reverse('production:production-order-detail', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete Order')
        self.assertNotContains(response, 'Cancel Order')

    def test_detail_view_shows_cancel_button_when_targets_not_met(self):
        """Test detail view shows Cancel Order button when production targets are not met"""
        # Don't add production results (targets not met)
        
        url = reverse('production:production-order-detail', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancel Order')
        self.assertNotContains(response, 'Complete Order')

    def test_detail_view_shows_progress_bars(self):
        """Test detail view shows progress bars for production items"""
        # Add partial production results
        self.create_production_result(self.product, 7)  # 70% of target
        
        url = reverse('production:production-order-detail', 
                     kwargs={'pk': self.production_order.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show progress information
        self.assertContains(response, 'progress')
        self.assertContains(response, '7')  # actual quantity
        self.assertContains(response, '10')  # planned quantity
