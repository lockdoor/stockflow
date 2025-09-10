"""
Tests for Production Process Confirmation functionality.
Testing the complete flow of confirming production processes and their effects on WIP stock.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from tests.factories.user import AdminFactory
from tests.factories.catalog import ItemFactory, ProductFactory
from tests.factories.inventory import WarehouseFactory
from tests.factories.production import ProductionOrderFactory, ProductionOrderBOMFactory

from production.models import ProductionProcess, ProductionResult, ProductionLoss, WIPStockMovement


class ProductionProcessConfirmationTests(TransactionTestCase):
    """Tests for production process confirmation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.admin = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin)
        
        # Create materials (items)
        self.material_1 = ItemFactory(name="Material 1", created_by=self.admin)
        self.material_2 = ItemFactory(name="Material 2", created_by=self.admin)
        
        # Create product manually to avoid auto BOM creation and activation
        from catalog.models import ItemSKU
        self.product = ItemSKU.objects.create(
            name="Test Product", 
            sku_code="TEST-PROD-001",  # Required field
            unit="pcs",  # Required field
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Keep as DRAFT to allow BOM editing
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Create BOM entries with predictable quantities for testing
        from catalog.models import BOM
        BOM.objects.create(
            parent_sku=self.product,
            component_sku=self.material_1,
            quantity=2,  # Need 2 units of material 1 per product
            created_by=self.admin,
            updated_by=self.admin
        )
        BOM.objects.create(
            parent_sku=self.product,
            component_sku=self.material_2,
            quantity=3,  # Need 3 units of material 2 per product
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Now activate the product to make BOM available for production
        self.product.status = ItemSKU.Status.ACTIVE
        self.product.save()
        
        # Create production order
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin
        )
        
        # Add BOM to production order
        ProductionOrderBOMFactory(
            production_order=self.production_order,
            item_sku=self.product,
            planned_quantity=10,
            created_by=self.admin
        )
        
        # Create production order
        self.production_order.created_production_order(self.admin)
        
        # Create production process
        self.production_process = ProductionProcess.objects.create(
            production_order=self.production_order,
            process_name="Test Process",
            note="Test process note",
            status=ProductionProcess.StatusChoices.DRAFT,
            created_by=self.admin,
            updated_by=self.admin
        )
    
    def test_draft_process_creation(self):
        """Test that production process can be created in DRAFT status."""
        self.assertEqual(self.production_process.status, ProductionProcess.StatusChoices.DRAFT)
        self.assertEqual(self.production_process.process_name, "Test Process")
        self.assertFalse(self.production_process.is_confirmed)
    
    def test_add_production_results(self):
        """Test adding production results to process."""
        result = ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=8,  # Produced 8 units out of planned 10
            created_by=self.admin,
            updated_by=self.admin
        )
        
        self.assertEqual(result.quantity, 8)
        self.assertEqual(result.item_sku, self.product)
    
    def test_add_production_losses(self):
        """Test adding production losses to process."""
        loss = ProductionLoss.objects.create(
            production_process=self.production_process,
            item_sku=self.material_1,
            quantity=2,  # Lost 2 units of material 1
            reason="Material defect",
            created_by=self.admin,
            updated_by=self.admin
        )
        
        self.assertEqual(loss.quantity, 2)
        self.assertEqual(loss.item_sku, self.material_1)
        self.assertEqual(loss.reason, "Material defect")
    
    def test_process_confirmation_basic(self):
        """Test basic production process confirmation."""
        # First, create WIP stock movements to bring materials into WIP
        # This simulates the materials being moved to production
        # For 8 units of product: need 8*2=16 of material_1, 8*3=24 of material_2
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_1,
            movement_type='IN',
            quantity=20,  # 20 > 16 needed for 8 products
            note='Material 1 moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_2,
            movement_type='IN',
            quantity=30,  # 30 > 24 needed for 8 products
            note='Material 2 moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Add results
        ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=8,
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Confirm process
        initial_wip_count = WIPStockMovement.objects.count()
        self.production_process.confirm_process(self.admin)
        
        # Check status changed
        self.production_process.refresh_from_db()
        self.assertEqual(self.production_process.status, ProductionProcess.StatusChoices.CONFIRMED)
        self.assertTrue(self.production_process.is_confirmed)
        
        # Check WIP movements created (should have more movements from confirmation)
        self.assertGreater(WIPStockMovement.objects.count(), initial_wip_count)
    
    def test_process_confirmation_with_losses(self):
        """Test production process confirmation with losses."""
        # First, create WIP stock movements to bring materials into WIP
        # For 7 units + 1 loss of material_1: need 7*2=14 + extra, 7*3=21 of material_2
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_1,
            movement_type='IN',
            quantity=25,  # Extra for losses and production
            note='Material 1 moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_2,
            movement_type='IN',
            quantity=30,  # 30 > 21 needed for 7 products
            note='Material 2 moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Add results and losses
        ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=7,
            created_by=self.admin,
            updated_by=self.admin
        )
        
        ProductionLoss.objects.create(
            production_process=self.production_process,
            item_sku=self.material_1,
            quantity=1,
            reason="Spillage",
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Confirm process
        self.production_process.confirm_process(self.admin)
        
        # Check status
        self.production_process.refresh_from_db()
        self.assertEqual(self.production_process.status, ProductionProcess.StatusChoices.CONFIRMED)
    
    def test_confirmed_process_immutable(self):
        """Test that confirmed processes cannot be modified."""
        # Create WIP stock first
        # Need sufficient for 8 units: 8*2=16 of material_1, 8*3=24 of material_2
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_1,
            movement_type='IN',
            quantity=20,  # 20 > 16 needed
            note='Material moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_2,
            movement_type='IN',
            quantity=30,  # 30 > 24 needed
            note='Material moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Confirm process first
        ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=8,
            created_by=self.admin,
            updated_by=self.admin
        )
        
        self.production_process.confirm_process(self.admin)
        
        # Try to modify - should raise ValidationError
        self.production_process.note = "Modified note"
        with self.assertRaises(ValidationError):
            self.production_process.full_clean()
    
    def test_integration_complete_flow(self):
        """Integration test for complete production process confirmation flow."""
        # Step 1: Create WIP stock movements to simulate materials being moved to production
        # For 8 units + 1 loss of material_1: need 8*2=16 + extra, 8*3=24 of material_2
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_1,
            movement_type='IN',
            quantity=25,  # Extra for losses and 8*2=16 needed
            note='Material 1 moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_2,
            movement_type='IN',
            quantity=30,  # 30 > 24 needed for 8 products
            note='Material 2 moved to WIP for production',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Step 2: Add production results
        result = ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=8,
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Step 3: Add production loss
        loss = ProductionLoss.objects.create(
            production_process=self.production_process,
            item_sku=self.material_1,
            quantity=1,
            reason="Material waste",
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Track initial state
        initial_wip_count = WIPStockMovement.objects.count()
        
        # Step 4: Confirm the process
        self.production_process.confirm_process(self.admin)
        
        # Verify final state
        self.production_process.refresh_from_db()
        
        # Status should be CONFIRMED
        self.assertEqual(self.production_process.status, ProductionProcess.StatusChoices.CONFIRMED)
        
        # WIP movements should be created (consumption and production)
        final_wip_count = WIPStockMovement.objects.count()
        self.assertGreater(final_wip_count, initial_wip_count)
        
        # Results and losses should still exist
        self.assertEqual(self.production_process.production_results.count(), 1)
        self.assertEqual(self.production_process.production_losses.count(), 1)
        
        # Verify specific data
        confirmed_result = self.production_process.production_results.first()
        confirmed_loss = self.production_process.production_losses.first()
        
        self.assertEqual(confirmed_result.quantity, 8)
        self.assertEqual(confirmed_loss.quantity, 1)
        self.assertEqual(confirmed_loss.reason, "Material waste")
    
    def test_process_confirmation_insufficient_wip_stock(self):
        """Test that process confirmation fails when WIP stock is insufficient."""
        # Only add small amount of WIP stock
        WIPStockMovement.objects.create(
            production_order=self.production_order,
            item_sku=self.material_1,
            movement_type='IN',
            quantity=1,  # Insufficient for production
            note='Small amount of Material 1',
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Add production results that would require more materials
        ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=8,  # This would require 8*2=16 material_1 and 8*3=24 material_2
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Confirmation should fail due to insufficient WIP stock
        with self.assertRaises(ValidationError) as context:
            self.production_process.confirm_process(self.admin)
        
        # Check that process remains in DRAFT status
        self.production_process.refresh_from_db()
        self.assertEqual(self.production_process.status, ProductionProcess.StatusChoices.DRAFT)
    
    def test_process_confirmation_no_wip_stock(self):
        """Test that process confirmation fails when no WIP stock exists."""
        # Don't create any WIP stock movements
        
        # Add production results
        ProductionResult.objects.create(
            production_process=self.production_process,
            item_sku=self.product,
            quantity=5,  # This would require 5*2=10 material_1 and 5*3=15 material_2
            created_by=self.admin,
            updated_by=self.admin
        )
        
        # Confirmation should fail due to no WIP stock
        with self.assertRaises(ValidationError):
            self.production_process.confirm_process(self.admin)
        
        # Process should remain in DRAFT status
        self.production_process.refresh_from_db()
        self.assertEqual(self.production_process.status, ProductionProcess.StatusChoices.DRAFT)


class ProductionProcessValidationTests(TestCase):
    """Tests for production process validation rules."""
    
    def setUp(self):
        """Set up test data."""
        self.admin = AdminFactory()
        self.warehouse = WarehouseFactory(created_by=self.admin)
        self.product = ProductFactory(name="Test Product", created_by=self.admin)
        
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin
        )
        
        self.production_process = ProductionProcess.objects.create(
            production_order=self.production_order,
            process_name="Test Process",
            status=ProductionProcess.StatusChoices.DRAFT,
            created_by=self.admin,
            updated_by=self.admin
        )
    
    def test_production_result_positive_quantity(self):
        """Test that production result quantity must be positive."""
        with self.assertRaises(ValidationError):
            result = ProductionResult(
                production_process=self.production_process,
                item_sku=self.product,
                quantity=-1,  # Negative quantity should fail
                created_by=self.admin,
                updated_by=self.admin
            )
            result.full_clean()
    
    def test_production_loss_positive_quantity(self):
        """Test that production loss quantity must be positive."""
        with self.assertRaises(ValidationError):
            loss = ProductionLoss(
                production_process=self.production_process,
                item_sku=self.product,
                quantity=0,  # Zero quantity should fail
                created_by=self.admin,
                updated_by=self.admin
            )
            loss.full_clean()
