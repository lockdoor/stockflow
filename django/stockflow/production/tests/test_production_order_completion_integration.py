"""
Integration Tests for Production Order Completion Feature

This module contains integration tests that verify the complete flow
of production order completion including edge cases and error scenarios.
"""

from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import transaction, IntegrityError
from unittest.mock import patch, Mock

from tests.factories import (
    WarehouseFactory,
    ProductionOrderFactory,
)
from tests.factories.user import AdminFactory
from catalog.models import ItemSKU, Category
from production.models import ProductionOrder, ProductionOrderBOM, WIPStockMovement
from production.models.production_process import ProductionProcess
from production.models.production_result import ProductionResult
from inventory.models import StockMovement, StockMovementItem, MaterialReservation

User = get_user_model()


class ProductionOrderCompletionIntegrationTests(TransactionTestCase):
    """Integration tests for complete production order flow"""
    
    def create_item(self, name, item_type=ItemSKU.Type.PRODUCT):
        """Helper method to create ItemSKU objects"""
        # Create category if needed
        category, _ = Category.objects.get_or_create(
            name="Test Category",
            defaults={
                'created_by': self.admin_user,
                'updated_by': self.admin_user
            }
        )
        
        # Determine initial status based on item type
        if item_type == ItemSKU.Type.RAW:
            # Raw materials can start as ACTIVE (no BOM required)
            initial_status = ItemSKU.Status.ACTIVE
        else:
            # Products should start as DRAFT (for BOM editing)
            initial_status = ItemSKU.Status.DRAFT
        
        # Create ItemSKU
        item = ItemSKU.objects.create(
            name=name,
            sku_code=f"SKU-{name.replace(' ', '')}-{ItemSKU.objects.count()}",
            unit="pcs",
            type=item_type,
            category=category,
            status=initial_status,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # For products, change to ACTIVE after creation
        if item_type == ItemSKU.Type.PRODUCT:
            item.status = ItemSKU.Status.ACTIVE
            item.save()
        
        return item
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create multiple products with different completion rates
        self.product1 = self.create_item("Product A", ItemSKU.Type.PRODUCT)
        self.product2 = self.create_item("Product B", ItemSKU.Type.PRODUCT)
        self.product3 = self.create_item("Product C", ItemSKU.Type.PRODUCT)
        
        # Create BOMs with different quantities
        self.bom1 = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product1,
            planned_quantity=Decimal('100.00'),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        self.bom2 = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product2,
            planned_quantity=Decimal('50.00'),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        self.bom3 = ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=self.product3,
            planned_quantity=Decimal('25.00'),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Progress through proper status transitions: DRAFT -> CREATED -> IN_PROGRESS
        self.production_order.status = ProductionOrder.Status.CREATED
        self.production_order.save()
        self.production_order.status = ProductionOrder.Status.IN_PROGRESS
        self.production_order.save()
        
        # Create materials for WIP testing
        self.material1 = self.create_item("Material A", ItemSKU.Type.RAW)
        self.material2 = self.create_item("Material B", ItemSKU.Type.RAW)
        
        self.client.force_login(self.admin_user)

    def create_production_results(self, product_quantities):
        """
        Helper to create production results for multiple products
        product_quantities: dict of {product: quantity}
        """
        for product, quantity in product_quantities.items():
            process = ProductionProcess.objects.create(
                production_order=self.production_order,
                status=ProductionProcess.StatusChoices.CONFIRMED,
                created_by=self.admin_user,
                updated_by=self.admin_user
            )
            ProductionResult.objects.create(
                production_process=process,
                item_sku=product,
                quantity=quantity,
                created_by=self.admin_user,
                updated_by=self.admin_user
            )

    def test_end_to_end_completion_flow_all_targets_met(self):
        """Test complete end-to-end flow when all production targets are met"""
        # Setup: Create production results that meet all targets
        self.create_production_results({
            self.product1: Decimal('100.00'),  # Exactly meets target
            self.product2: Decimal('55.00'),   # Exceeds target
            self.product3: Decimal('25.00'),   # Exactly meets target
        })
        
        # Verify initial state
        self.assertTrue(self.production_order.can_complete_production())
        
        # Step 1: Access completion confirmation page
        confirm_url = reverse('production:production-order-complete-confirm', 
                            kwargs={'pk': self.production_order.id})
        # Add HTTP_REFERER for template compatibility
        confirm_response = self.client.get(confirm_url, HTTP_REFERER='/production/orders/')
        self.assertEqual(confirm_response.status_code, 200)
        self.assertContains(confirm_response, 'Production Target Met')
        
        # Step 2: Submit completion
        complete_url = reverse('production:production-order-complete', 
                             kwargs={'pk': self.production_order.id})
        completion_data = {
            'confirm_complete': 'on',
            'completion_reason': 'All targets achieved successfully'
        }
        
        with transaction.atomic():
            complete_response = self.client.post(complete_url, completion_data)
        
        # Verify response
        self.assertEqual(complete_response.status_code, 302)
        
        # Verify production order status
        self.production_order.refresh_from_db()
        self.assertEqual(self.production_order.status, ProductionOrder.Status.CLOSED_COMPLETED)
        self.assertIn('[COMPLETED] All targets achieved successfully', self.production_order.note)


class ProductionOrderCompletionEdgeCaseTests(TestCase):
    """Test edge cases and error scenarios for production order completion"""
    
    def create_item(self, name, item_type=ItemSKU.Type.PRODUCT):
        """Helper method to create ItemSKU objects"""
        # Create category if needed
        category, _ = Category.objects.get_or_create(
            name="Test Category",
            defaults={
                'created_by': self.admin_user,
                'updated_by': self.admin_user
            }
        )
        
        # Determine initial status based on item type
        if item_type == ItemSKU.Type.RAW:
            # Raw materials can start as ACTIVE (no BOM required)
            initial_status = ItemSKU.Status.ACTIVE
        else:
            # Products should start as DRAFT (for BOM editing)
            initial_status = ItemSKU.Status.DRAFT
        
        # Create ItemSKU
        item = ItemSKU.objects.create(
            name=name,
            sku_code=f"SKU-{name.replace(' ', '')}-{ItemSKU.objects.count()}",
            unit="pcs",
            type=item_type,
            category=category,
            status=initial_status,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # For products, change to ACTIVE after creation
        if item_type == ItemSKU.Type.PRODUCT:
            item.status = ItemSKU.Status.ACTIVE
            item.save()
        
        return item
    
    def setUp(self):
        self.admin_user = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin_user)
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create a basic BOM to allow status transition
        product = self.create_item("Test Product", ItemSKU.Type.PRODUCT)
        ProductionOrderBOM.objects.create(
            production_order=self.production_order,
            item_sku=product,
            planned_quantity=Decimal('10.00'),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Progress through proper status transitions: DRAFT -> CREATED -> IN_PROGRESS
        self.production_order.status = ProductionOrder.Status.CREATED
        self.production_order.save()
        self.production_order.status = ProductionOrder.Status.IN_PROGRESS
        self.production_order.save()
        self.client.force_login(self.admin_user)

    def test_completion_with_zero_planned_quantities(self):
        """Test edge case with zero planned quantities"""
        # Create a separate production order for this test to avoid interference
        standalone_po = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Create zero-planned BOM while production order is in DRAFT status
        product = self.create_item("Zero Product", ItemSKU.Type.PRODUCT)
        bom = ProductionOrderBOM.objects.create(
            production_order=standalone_po,
            item_sku=product,
            planned_quantity=Decimal('0.00'),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Progress through status transitions: DRAFT -> CREATED -> IN_PROGRESS
        standalone_po.status = ProductionOrder.Status.CREATED
        standalone_po.save()
        standalone_po.status = ProductionOrder.Status.IN_PROGRESS
        standalone_po.save()
        
        # Even with zero planned, if there's any actual production, it should be "complete"
        process = ProductionProcess.objects.create(
            production_order=standalone_po,
            status=ProductionProcess.StatusChoices.CONFIRMED,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        ProductionResult.objects.create(
            production_process=process,
            item_sku=product,
            quantity=Decimal('5.00'),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Should be considered complete (actual >= planned, even if planned is 0)
        self.assertTrue(standalone_po.is_production_complete())
