from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM
from catalog.views.bom_views import BomUpdateView
from decimal import Decimal


class BomUpdateViewTest(TestCase):
    """
    Test BomUpdateView - Focus on view behavior, permissions, form handling, and HTMX responses.
    """
    
    def setUp(self):
        """Set up test data for BOM update view tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='testuser@example.com'
        )
        
        # Add permissions for BOM modification
        permission = Permission.objects.get(codename='change_bom')
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
        
        # Create existing BOM
        self.bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku1,
            quantity=Decimal('2.0'),
            created_by=self.user,
            updated_by=self.user
        )

    # =================================
    # VIEW ACCESS TESTS
    # =================================
    
    def test_view_requires_login(self):
        """Test that BomUpdateView requires login"""
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_view_requires_permission(self):
        """Test that BomUpdateView requires proper permission"""
        # Create user without permission
        user_no_perm = User.objects.create_user(
            username='noperm', 
            password='testpassword'
        )
        self.client.login(username='noperm', password='testpassword')
        
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Permission denied
        
    def test_view_with_authenticated_user_and_permission(self):
        """Test BomUpdateView with authenticated user and proper permission"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_bom_id_returns_404(self):
        """Test BomUpdateView with invalid BOM ID returns 404"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # =================================
    # CONTEXT DATA TESTS
    # =================================
    
    def test_view_context_data_includes_required_objects(self):
        """Test that context includes categories, bom, and parent_sku"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('category', response.context)
        self.assertIn('bom', response.context)
        self.assertIn('parent_sku', response.context)
        self.assertEqual(response.context['bom'], self.bom)
        self.assertEqual(response.context['parent_sku'], self.parent_sku)
        
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
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        response = self.client.get(url)
        
        categories = list(response.context['category'])
        category_names = [cat.name for cat in categories]
        self.assertEqual(category_names, sorted(category_names))

    # =================================
    # FORM SUBMISSION TESTS
    # =================================
    
    def test_form_valid_updates_bom(self):
        """Test successful BOM update"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': '3.5'  # Updated quantity
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        
        # Check BOM was updated
        updated_bom = BOM.objects.get(pk=self.bom.id)
        self.assertEqual(updated_bom.quantity, Decimal('3.5'))
        self.assertEqual(updated_bom.updated_by, self.user)
        
        # Check parent and component remain unchanged
        self.assertEqual(updated_bom.parent_sku, self.parent_sku)
        self.assertEqual(updated_bom.component_sku, self.component_sku1)
        
    def test_form_valid_returns_htmx_response(self):
        """Test that successful form submission returns proper HTMX response"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': '1.5'
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'success')
        
    def test_form_invalid_returns_form_with_errors(self):
        """Test that invalid form returns errors"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        # Invalid form data (zero quantity)
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': '0'  # Invalid quantity
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
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        # Invalid form data
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': 'invalid'  # Invalid quantity
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('bom', response.context)
        self.assertIn('parent_sku', response.context)
        self.assertIn('category', response.context)
        self.assertIn('form_errors', response.context)
        self.assertIn('error_message', response.context)

    # =================================
    # FIELD RESTRICTION TESTS
    # =================================
    
    def test_form_prevents_parent_sku_change(self):
        """Test that form preserves original parent_sku even if different value submitted"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        # Try to change parent_sku (should be preserved by disabled field)
        form_data = {
            'parent_sku': self.component_sku2.id,  # Different parent
            'component_sku': self.component_sku1.id,
            'quantity': '2.0'
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        
        # Check BOM was updated but parent_sku remained unchanged
        updated_bom = BOM.objects.get(pk=self.bom.id)
        self.assertEqual(updated_bom.parent_sku, self.parent_sku)  # Should remain unchanged
        
    def test_form_prevents_component_sku_change(self):
        """Test that form preserves original component_sku even if different value submitted"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        # Try to change component_sku (should be preserved by disabled field)
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku2.id,  # Different component
            'quantity': '2.0'
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        
        # Check BOM was updated but component_sku remained unchanged
        updated_bom = BOM.objects.get(pk=self.bom.id)
        self.assertEqual(updated_bom.component_sku, self.component_sku1)  # Should remain unchanged

    # =================================
    # BUSINESS LOGIC VALIDATION TESTS
    # =================================
    
    def test_form_handles_business_logic_validation_errors(self):
        """Test that business logic validation errors are handled properly"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        # Try to update with negative quantity (should fail business logic)
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': '-1.0'
        }
        
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    # =================================
    # VIEW CLASS TESTS
    # =================================
    
    def test_view_class_attributes(self):
        """Test BomUpdateView class attributes"""
        view = BomUpdateView()
        
        self.assertEqual(view.model, BOM)
        self.assertEqual(view.template_name, 'catalog/bom/partials/bom-form.html')
        self.assertEqual(view.permission_required, 'catalog.change_bom')
        self.assertEqual(view.pk_url_kwarg, 'pk')
        
    def test_view_class_mixins(self):
        """Test BomUpdateView inherits from correct mixins"""
        from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
        from django.views.generic import UpdateView
        
        self.assertTrue(issubclass(BomUpdateView, LoginRequiredMixin))
        self.assertTrue(issubclass(BomUpdateView, PermissionRequiredMixin))
        self.assertTrue(issubclass(BomUpdateView, UpdateView))

    # =================================
    # TEMPLATE TESTS
    # =================================
    
    def test_view_uses_correct_template(self):
        """Test that BomUpdateView uses correct template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'catalog/bom/partials/bom-form.html')

    # =================================
    # QUANTITY UPDATE EDGE CASES
    # =================================
    
    def test_quantity_update_with_decimal_values(self):
        """Test quantity update with various decimal values"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:bom-edit', kwargs={'pk': self.bom.id})
        
        test_quantities = ['0.01', '1.25', '10.75', '999.99']
        
        for qty in test_quantities:
            with self.subTest(quantity=qty):
                form_data = {
                    'parent_sku': self.parent_sku.id,
                    'component_sku': self.component_sku1.id,
                    'quantity': qty
                }
                
                response = self.client.post(url, data=form_data)
                self.assertEqual(response.status_code, 200)
                
                # Check BOM was updated
                updated_bom = BOM.objects.get(pk=self.bom.id)
                self.assertEqual(str(updated_bom.quantity), qty)
