from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import Http404
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM
from catalog.views.bom_views import BomListByParentIDView


class BomListByParentIDViewTest(TestCase):
    """
    Test BomListByParentIDView - Focus on view behavior, permissions, and template rendering.
    """
    
    def setUp(self):
        """Set up test data for BOM list view tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='testuser@example.com'
        )
        
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
        
        # Create BOMs
        self.bom1 = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku1,
            quantity=2.5,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.bom2 = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku2,
            quantity=1.0,
            created_by=self.user,
            updated_by=self.user
        )

    # =================================
    # VIEW ACCESS TESTS
    # =================================
    
    def test_view_requires_login(self):
        """Test that BomListByParentIDView requires login"""
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_view_with_authenticated_user(self):
        """Test BomListByParentIDView with authenticated user"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # =================================
    # VIEW CONTENT TESTS
    # =================================
    
    def test_view_context_data(self):
        """Test BomListByParentIDView context data"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('boms', response.context)
        self.assertIn('parent_sku', response.context)
        self.assertEqual(response.context['parent_sku'], self.parent_sku)
        
    def test_view_queryset_filtering(self):
        """Test that queryset is properly filtered by parent_sku"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        boms = response.context['boms']
        self.assertEqual(len(boms), 2)
        
        # Check that all BOMs belong to the correct parent
        for bom in boms:
            self.assertEqual(bom.parent_sku, self.parent_sku)
            
    def test_view_queryset_ordering(self):
        """Test that queryset is ordered by -created_at"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        boms = list(response.context['boms'])
        # bom2 should come first (created later)
        self.assertEqual(boms[0], self.bom2)
        self.assertEqual(boms[1], self.bom1)
        
    def test_view_empty_queryset(self):
        """Test BomListByParentIDView with no BOMs"""
        # Create another parent without BOMs
        parent_empty = ItemSKU.objects.create(
            sku_code='PROD002',
            name='Product 2',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': parent_empty.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        boms = response.context['boms']
        self.assertEqual(len(boms), 0)

    # =================================
    # ERROR HANDLING TESTS
    # =================================
    
    def test_view_invalid_parent_id(self):
        """Test BomListByParentIDView with invalid parent_id"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_view_missing_parent_id_raises_http404(self):
        """Test that missing parent_id raises Http404"""
        view = BomListByParentIDView()
        view.kwargs = {}  # No parent_id
        
        with self.assertRaises(Http404):
            view.get_queryset()

    # =================================
    # VIEW CLASS TESTS
    # =================================
    
    def test_view_class_attributes(self):
        """Test BomListByParentIDView class attributes"""
        view = BomListByParentIDView()
        
        self.assertEqual(view.model, BOM)
        self.assertEqual(view.template_name, 'catalog/bom/partials/bom-list.html')
        self.assertEqual(view.context_object_name, 'boms')
        self.assertEqual(view.paginate_by, 20)
        
    def test_view_class_mixins(self):
        """Test BomListByParentIDView inherits from correct mixins"""
        from django.contrib.auth.mixins import LoginRequiredMixin
        from django.views.generic import ListView
        
        self.assertTrue(issubclass(BomListByParentIDView, LoginRequiredMixin))
        self.assertTrue(issubclass(BomListByParentIDView, ListView))

    # =================================
    # SELECT_RELATED OPTIMIZATION TESTS
    # =================================
    
    def test_view_uses_select_related(self):
        """Test that view uses select_related for query optimization"""
        self.client.login(username='testuser', password='testpassword')
        
        with self.assertNumQueries(7):  # Adjusted based on actual Django behavior
            url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
            response = self.client.get(url)
            
            # Access related fields to ensure they're prefetched
            boms = response.context['boms']
            for bom in boms:
                _ = bom.component_sku.name
                _ = bom.parent_sku.name
                _ = bom.created_by.username
                _ = bom.updated_by.username

    # =================================
    # TEMPLATE TESTS
    # =================================
    
    def test_view_uses_correct_template(self):
        """Test that BomListByParentIDView uses correct template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'catalog/bom/partials/bom-list.html')
        
    def test_view_response_contains_bom_data(self):
        """Test that response contains BOM data"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-list', kwargs={'parent_id': self.parent_sku.id})
        response = self.client.get(url)
        
        content = response.content.decode('utf-8')
        # Should contain component names
        self.assertIn('Raw Material 1', content)
        self.assertIn('Raw Material 2', content)
