from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.http import Http404
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM
from catalog.views.bom_views import BomCreateView
from decimal import Decimal


class BomCreateViewTest(TestCase):
    """
    Test BomCreateView - Focus on view behavior, permissions, form handling, and HTMX responses.
    """
    
    def setUp(self):
        """Set up test data for BOM create view tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='testuser@example.com'
        )
        
        # Add permissions for BOM creation
        permission = Permission.objects.get(codename='add_bom')
        self.user.user_permissions.add(permission)
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for BOM view tests',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create parent item (PRODUCT in DRAFT status)
        self.parent_sku = ItemSKU.objects.create(
            sku_code='PROD001',
            name='Product 1',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create component items
        self.component_sku1 = ItemSKU.objects.create(
            sku_code='RAW001',
            name='Raw Material 1',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.component_sku2 = ItemSKU.objects.create(
            sku_code='RAW002',
            name='Raw Material 2',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )

    # =================================
    # VIEW ACCESS TESTS
    # =================================
    
    def test_view_requires_login(self):
        """Test that BomCreateView requires login"""
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_view_requires_permission(self):
        """Test that BomCreateView requires proper permission"""
        # Create user without permission
        user_no_perm = User.objects.create_user(
            username='noperm', 
            password='testpassword'
        )
        self.client.login(username='noperm', password='testpassword')
        
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Permission denied
        
    def test_view_with_authenticated_user_and_permission(self):
        """Test BomCreateView with authenticated user and proper permission"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # =================================
    # VIEW INITIALIZATION TESTS
    # =================================
    
    def test_view_get_initial_sets_parent_sku(self):
        """Test that get_initial properly sets parent_sku"""
        view = BomCreateView()
        view.kwargs = {'parent_id': self.parent_sku.id}
        
        initial = view.get_initial()
        self.assertEqual(view.parent_sku, self.parent_sku)
        
    def test_view_get_initial_missing_parent_id_raises_http404(self):
        """Test that missing parent_id raises Http404"""
        view = BomCreateView()
        view.kwargs = {}  # No parent_id
        
        with self.assertRaises(Http404):
            view.get_initial()
            
    def test_view_get_initial_invalid_parent_id_raises_404(self):
        """Test that invalid parent_id raises 404"""
        view = BomCreateView()
        view.kwargs = {'parent_id': 99999}  # Non-existent ID
        
        with self.assertRaises(Http404):
            view.get_initial()

    # =================================
    # CONTEXT DATA TESTS
    # =================================
    
    def test_view_context_data_includes_categories_and_parent(self):
        """Test that context includes categories and parent_sku"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('category', response.context)
        self.assertIn('parent_sku', response.context)
        self.assertEqual(response.context['parent_sku'], self.parent_sku)
        
        # Check categories are ordered by name
        categories = list(response.context['category'])
        self.assertTrue(len(categories) > 0)
        
    def test_view_context_data_categories_ordered_by_name(self):
        """Test that categories are ordered by name"""
        # Create additional categories to test ordering
        cat_z = Category.objects.create(
            name='Z Category',
            created_by=self.user,
            updated_by=self.user
        )
        cat_a = Category.objects.create(
            name='A Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        categories = list(response.context['category'])
        category_names = [cat.name for cat in categories]
        self.assertEqual(category_names, sorted(category_names))

    # =================================
    # FORM KWARGS TESTS
    # =================================
    
    def test_view_get_form_kwargs_includes_parent_sku(self):
        """Test that form kwargs include parent_sku"""
        view = BomCreateView()
        view.kwargs = {'parent_id': self.parent_sku.id}
        # Need to simulate request for form kwargs
        from django.test import RequestFactory
        factory = RequestFactory()
        view.request = factory.get('/')
        view.get_initial()  # This sets parent_sku
        
        kwargs = view.get_form_kwargs()
        self.assertIn('parent_sku', kwargs)
        self.assertEqual(kwargs['parent_sku'], self.parent_sku)

    # =================================
    # FORM SUBMISSION TESTS
    # =================================
    
    def test_form_valid_creates_bom(self):
        """Test successful BOM creation"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        
        form_data = {
            'quantity': '2.5',
            'component_sku': self.component_sku1.id
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        
        # Check BOM was created
        bom = BOM.objects.filter(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku1
        ).first()
        self.assertIsNotNone(bom)
        self.assertEqual(bom.quantity, Decimal('2.5'))
        self.assertEqual(bom.created_by, self.user)
        self.assertEqual(bom.updated_by, self.user)
        
    def test_form_valid_returns_htmx_response(self):
        """Test that successful form submission returns proper HTMX response"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        
        form_data = {
            'quantity': '1.0',
            'component_sku': self.component_sku1.id
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'success')
        
    def test_form_invalid_returns_form_with_errors(self):
        """Test that invalid form returns errors"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        
        # Invalid form data (missing quantity)
        form_data = {
            'component_sku': self.component_sku1.id
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(response['HX-Retarget'], '#bom-form-container')
        self.assertEqual(response['HX-Reswap'], 'innerHTML')
        
    def test_form_invalid_includes_context_data(self):
        """Test that form_invalid includes necessary context data"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        
        # Invalid form data
        form_data = {
            'quantity': 'invalid'
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('parent_sku', response.context)
        self.assertIn('category', response.context)
        self.assertIn('form_errors', response.context)
        self.assertIn('error_message', response.context)

    # =================================
    # BUSINESS LOGIC VALIDATION TESTS
    # =================================
    
    def test_form_handles_business_logic_validation_errors(self):
        """Test that business logic validation errors are handled properly"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        
        # Try to create BOM with zero quantity (should fail business logic)
        form_data = {
            'quantity': '0',
            'component_sku': self.component_sku1.id
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        
    def test_form_handles_duplicate_bom_creation(self):
        """Test handling of duplicate BOM creation"""
        # Create initial BOM
        BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku1,
            quantity=1.0,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        
        # Try to create duplicate BOM
        form_data = {
            'quantity': '2.0',
            'component_sku': self.component_sku1.id
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    # =================================
    # VIEW CLASS TESTS
    # =================================
    
    def test_view_class_attributes(self):
        """Test BomCreateView class attributes"""
        view = BomCreateView()
        
        self.assertEqual(view.model, BOM)
        self.assertEqual(view.template_name, 'catalog/bom/partials/bom-form.html')
        self.assertEqual(view.permission_required, 'catalog.add_bom')
        
    def test_view_class_mixins(self):
        """Test BomCreateView inherits from correct mixins"""
        from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
        from django.views.generic import CreateView
        
        self.assertTrue(issubclass(BomCreateView, LoginRequiredMixin))
        self.assertTrue(issubclass(BomCreateView, PermissionRequiredMixin))
        self.assertTrue(issubclass(BomCreateView, CreateView))

    # =================================
    # TEMPLATE TESTS
    # =================================
    
    def test_view_uses_correct_template(self):
        """Test that BomCreateView uses correct template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'catalog/bom/partials/bom-form.html')

    # =================================
    # ERROR HANDLING EDGE CASES
    # =================================
    
    def test_view_handles_invalid_parent_id_in_url(self):
        """Test view handles invalid parent_id gracefully"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-create', kwargs={'parent_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
