"""
Test for enhanced WarehousePermissionMixin with stock_movement_id support

Tests the ability of WarehousePermissionMixin to resolve warehouse_id
from stock_movement_id in URL kwargs.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.warehouse import Warehouse
from inventory.mixins.warehouse import WarehousePermissionMixin


class TestViewWithStockMovementId(WarehousePermissionMixin):
    """Test view to simulate StockItemMovementCreateView behavior"""
    permission_required_base = 'add_stockmovementitem'
    
    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs


class WarehousePermissionMixinEnhancedTest(TestCase):
    """Test enhanced WarehousePermissionMixin with stock_movement_id support"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create warehouse - this will trigger permission creation
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            address='123 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movement
        self.stock_movement = StockMovement(
            warehouse=self.warehouse,
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=123,
            note='Test movement',
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        super(StockMovement, self.stock_movement).save()
        
        # Get permissions
        stock_movement_item_content_type = ContentType.objects.get_for_model(StockMovementItem)
        self.base_permission = Permission.objects.get(
            codename='add_stockmovementitem',
            content_type=stock_movement_item_content_type
        )
        
        self.warehouse_permission = Permission.objects.get(
            codename=f'can_manage_warehouse_{self.warehouse.id}'
        )

    def test_get_warehouse_id_from_stock_movement_id(self):
        """Test that warehouse_id is correctly resolved from stock_movement_id"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id=self.stock_movement.id
        )
        
        warehouse_id = view.get_warehouse_id()
        self.assertEqual(warehouse_id, self.warehouse.id)

    def test_get_warehouse_id_with_nonexistent_stock_movement(self):
        """Test handling of non-existent stock movement"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id=99999  # Non-existent
        )
        
        warehouse_id = view.get_warehouse_id()
        self.assertIsNone(warehouse_id)

    def test_permission_check_with_stock_movement_id_and_base_permission(self):
        """Test permission check works with stock_movement_id and base permission"""
        self.user.user_permissions.add(self.base_permission)
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id=self.stock_movement.id
        )
        
        # Should pass because user has base permission
        self.assertTrue(view.test_func())

    def test_permission_check_with_stock_movement_id_and_warehouse_permission(self):
        """Test permission check works with stock_movement_id and warehouse permission"""
        self.user.user_permissions.add(self.warehouse_permission)
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id=self.stock_movement.id
        )
        
        # Should pass because user has warehouse-specific permission
        self.assertTrue(view.test_func())

    def test_permission_check_fails_without_permission(self):
        """Test permission check fails without any permission"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id=self.stock_movement.id
        )
        
        # Should fail because user has no permission
        self.assertFalse(view.test_func())

    def test_warehouse_id_priority_order(self):
        """Test that warehouse_id takes priority over stock_movement_id"""
        request = self.factory.get('/')
        request.user = self.user
        
        # Create another warehouse
        warehouse2 = Warehouse(
            name='Warehouse 2',
            code='TEST02',
            address='456 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, warehouse2).save()
        
        view = TestViewWithStockMovementId(
            request,
            warehouse_id=warehouse2.id,  # Direct warehouse_id
            stock_movement_id=self.stock_movement.id  # Should be ignored
        )
        
        warehouse_id = view.get_warehouse_id()
        # Should return warehouse2.id, not self.warehouse.id
        self.assertEqual(warehouse_id, warehouse2.id)

    def test_get_warehouse_id_returns_none_without_kwargs(self):
        """Test that get_warehouse_id returns None when no relevant kwargs"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(request)  # No kwargs
        
        warehouse_id = view.get_warehouse_id()
        self.assertIsNone(warehouse_id)

    def test_permission_check_without_warehouse_falls_back_to_base(self):
        """Test that without warehouse_id, only base permission is checked"""
        self.user.user_permissions.add(self.base_permission)
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(request)  # No kwargs
        
        # Should pass because user has base permission
        self.assertTrue(view.test_func())

    def test_handle_no_permission_with_stock_movement_context(self):
        """Test error message includes warehouse context when derived from stock movement"""
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id=self.stock_movement.id
        )
        
        with self.assertRaises(PermissionDenied) as cm:
            view.handle_no_permission()
        
        error_message = str(cm.exception)
        self.assertIn(str(self.warehouse.id), error_message)
        self.assertIn('add_stockmovementitem', error_message)

    def test_integration_with_different_warehouse_permissions(self):
        """Test that warehouse-specific permission only works for correct warehouse"""
        # Create another warehouse and stock movement
        warehouse2 = Warehouse(
            name='Warehouse 2',
            code='TEST02',
            address='456 Test St',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, warehouse2).save()
        
        movement2 = StockMovement(
            warehouse=warehouse2,
            reference_type=StockMovement.ReferenceType.ADJUST,
            reference_id=456,
            note='Test movement 2',
            status=StockMovement.Status.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        super(StockMovement, movement2).save()
        
        # Give user permission only for warehouse1
        self.user.user_permissions.add(self.warehouse_permission)
        
        request = self.factory.get('/')
        request.user = self.user
        
        # Test access to warehouse1 stock movement (should work)
        view1 = TestViewWithStockMovementId(
            request,
            stock_movement_id=self.stock_movement.id
        )
        self.assertTrue(view1.test_func())
        
        # Test access to warehouse2 stock movement (should fail)
        view2 = TestViewWithStockMovementId(
            request,
            stock_movement_id=movement2.id
        )
        self.assertFalse(view2.test_func())

    def test_exception_handling_in_get_warehouse_id(self):
        """Test that exceptions in get_warehouse_id are handled gracefully"""
        request = self.factory.get('/')
        request.user = self.user
        
        # Test with invalid stock_movement_id type
        view = TestViewWithStockMovementId(
            request,
            stock_movement_id='invalid'
        )
        
        # Should return None instead of raising exception
        warehouse_id = view.get_warehouse_id()
        self.assertIsNone(warehouse_id)
