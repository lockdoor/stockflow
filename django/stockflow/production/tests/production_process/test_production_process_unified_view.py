from django.test import TestCase, client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from tests.factories.user import UserFactory


class ProductionProcessUnifiedViewTestsSimple(TestCase):
    """
    Simple tests that don't use complex factories to avoid BOM issues
    """
    def setUp(self):
        from tests.factories.user import UserFactory
        from tests.factories.inventory import WarehouseFactory
        from tests.factories.production import ProductionOrderFactory
        
        # Create basic users
        self.admin_user = UserFactory(username='admin', password='password', is_staff=True, is_superuser=True)
        self.regular_user = UserFactory(username='regular_user', password='testpass123')
        self.warehouse_user = UserFactory(username='warehouse_user', password='testpass123')
        
        # Create warehouse
        self.warehouse = WarehouseFactory(name="Test Warehouse", created_by=self.admin_user)
        
        # Create simple production order without complex BOM
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user
        )
        
        self.client = client.Client()
        self.create_url = reverse('production:production-process-unified-create', 
                                args=[self.production_order.id])
        
        # Assign warehouse user to this warehouse
        self.warehouse.assign_user(self.warehouse_user)

    def test_warehouse_permission_system_works(self):
        """Test basic warehouse permission functionality"""
        # Regular user should not have access
        self.assertFalse(self.warehouse.has_user_access(self.regular_user))
        
        # Warehouse user should have access
        self.assertTrue(self.warehouse.has_user_access(self.warehouse_user))
        
        # Admin should have access
        self.assertTrue(self.warehouse.has_user_access(self.admin_user))

    def test_view_requires_login(self):
        """Test that anonymous users are redirected to login"""
        response = self.client.get(self.create_url)
        # Status code can be either 302 (redirect) or 403 (forbidden)
        # Both indicate authentication is required
        self.assertIn(response.status_code, [302, 403])
        
        if response.status_code == 302:
            self.assertRedirects(response, f"{reverse('login')}?next={self.create_url}")
        else:
            # If it's 403, that also means authentication is required
            self.assertEqual(response.status_code, 403)

    def test_user_assignment_to_warehouse(self):
        """Test adding and removing users from warehouse"""
        # Initially other user should not have access
        other_user = UserFactory(username='other_user', password='testpass123')
        self.assertFalse(self.warehouse.has_user_access(other_user))
        
        # Assign user to warehouse
        success = self.warehouse.assign_user(other_user)
        self.assertTrue(success)
        self.assertTrue(self.warehouse.has_user_access(other_user))
        
        # Remove user from warehouse  
        success = self.warehouse.remove_user(other_user)
        self.assertTrue(success)
        self.assertFalse(self.warehouse.has_user_access(other_user))

    def test_get_user_warehouses(self):
        """Test getting warehouses accessible to user"""
        from inventory.models import Warehouse
        
        # Regular user should have no warehouses
        regular_warehouses = Warehouse.get_user_warehouses(self.regular_user)
        self.assertEqual(regular_warehouses.count(), 0)
        
        # Warehouse user should have access to their warehouse
        user_warehouses = Warehouse.get_user_warehouses(self.warehouse_user)
        self.assertEqual(user_warehouses.count(), 1)
        self.assertEqual(user_warehouses.first().id, self.warehouse.id)

    def test_unified_view_access_control(self):
        """Test access control for unified view"""
        # Regular user should not have access
        self.client.login(username=self.regular_user.username, password='testpass123')
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 403)
        
        # Warehouse user should have access
        self.client.login(username=self.warehouse_user.username, password='testpass123')
        response = self.client.get(self.create_url)
        self.assertIn(response.status_code, [200, 302])
        
        # Admin user should have access
        self.client.login(username=self.admin_user.username, password='password')
        response = self.client.get(self.create_url)
        self.assertIn(response.status_code, [200, 302]) 

    def test_cross_warehouse_access_denied(self):
        """Test that users can't access other warehouses' production orders"""
        from tests.factories.inventory import WarehouseFactory
        from tests.factories.production import ProductionOrderFactory
        
        # Create another warehouse and production order
        other_warehouse = WarehouseFactory(name="Other Warehouse", created_by=self.admin_user)
        other_production_order = ProductionOrderFactory(
            warehouse=other_warehouse, 
            created_by=self.admin_user
        )
        
        other_url = reverse('production:production-process-unified-create', 
                        args=[other_production_order.id])
        
        # Warehouse user should not be able to access other warehouse
        self.client.login(username=self.warehouse_user.username, password='testpass123')
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 403)

class ProductionProcessDetailViewTestsSimple(TestCase):
    """
    Simple tests for ProductionProcessDetailView without complex factories
    """
    def setUp(self):
        from tests.factories.user import UserFactory
        from tests.factories.inventory import WarehouseFactory
        from tests.factories.production import ProductionOrderFactory
        from production.models import ProductionProcess
        
        # Create basic users
        self.admin_user = UserFactory(username='admin', password='password', is_staff=True, is_superuser=True)
        self.regular_user = UserFactory(username='regular_user', password='testpass123')
        self.warehouse_user = UserFactory(username='warehouse_user', password='testpass123')
        
        # Create warehouse
        self.warehouse = WarehouseFactory(name="Test Warehouse", created_by=self.admin_user)
        
        # Create simple production order without complex BOM
        self.production_order = ProductionOrderFactory(
            warehouse=self.warehouse,
            created_by=self.admin_user
        )
        
        # Create confirmed production process
        self.production_process = ProductionProcess.objects.create(
            production_order=self.production_order,
            status='CONFIRMED',
            process_name='Test Production Process',
            started_at=timezone.now() - timezone.timedelta(hours=2),
            finished_at=timezone.now() - timezone.timedelta(hours=1),
            note='Test confirmed process',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        self.client = client.Client()
        self.detail_url = reverse('production:production-process-detail', 
                                args=[self.production_order.id, self.production_process.id])
        
        # Assign warehouse user to this warehouse
        self.warehouse.assign_user(self.warehouse_user)

    def test_view_requires_login(self):
        """Test that anonymous users are redirected to login"""
        response = self.client.get(self.detail_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.detail_url}")

    def test_view_requires_warehouse_permission(self):
        """Test that users without warehouse permission get 403"""
        self.client.login(username=self.regular_user.username, password='testpass123')
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 403)

    def test_warehouse_user_can_access_confirmed_process(self):
        """Test that users with warehouse permission can access confirmed process"""
        self.client.login(username=self.warehouse_user.username, password='testpass123')
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('process', response.context)
        self.assertEqual(response.context['process'].id, self.production_process.id)

    def test_admin_user_can_access_confirmed_process(self):
        """Test that admin user can access any warehouse's confirmed process"""
        self.client.login(username=self.admin_user.username, password='password')
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_only_confirmed_processes_accessible(self):
        """Test that only CONFIRMED status processes are accessible"""
        from production.models import ProductionProcess
        
        # Create a non-confirmed process
        draft_process = ProductionProcess.objects.create(
            production_order=self.production_order,
            status='DRAFT',
            process_name='Test Draft Process',
            started_at=timezone.now() - timezone.timedelta(hours=1),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        draft_url = reverse('production:production-process-detail', 
                          args=[self.production_order.id, draft_process.id])
        
        self.client.login(username=self.warehouse_user.username, password='testpass123')
        response = self.client.get(draft_url)
        self.assertEqual(response.status_code, 404)

    def test_cross_warehouse_access_denied(self):
        """Test that users can't access other warehouses' production processes"""
        from tests.factories.inventory import WarehouseFactory
        from tests.factories.production import ProductionOrderFactory
        from production.models import ProductionProcess
        
        # Create another warehouse and production order/process
        other_warehouse = WarehouseFactory(name="Other Warehouse", created_by=self.admin_user)
        other_production_order = ProductionOrderFactory(
            warehouse=other_warehouse,
            created_by=self.admin_user
        )
        
        other_process = ProductionProcess.objects.create(
            production_order=other_production_order,
            status='CONFIRMED',
            process_name='Test Other Process',
            started_at=timezone.now() - timezone.timedelta(hours=1),
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        other_detail_url = reverse('production:production-process-detail', 
                                 args=[other_production_order.id, other_process.id])
        
        # Warehouse user should not be able to access other warehouse
        self.client.login(username=self.warehouse_user.username, password='testpass123')
        response = self.client.get(other_detail_url)
        self.assertEqual(response.status_code, 403)

    def test_context_includes_production_process(self):
        """Test that context includes production process"""
        self.client.login(username=self.warehouse_user.username, password='testpass123')
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that context uses 'process' not 'production_process'
        production_process = response.context['process']
        self.assertEqual(production_process.id, self.production_process.id)
        self.assertTrue(hasattr(production_process, 'production_results'))
        self.assertTrue(hasattr(production_process, 'production_losses'))
