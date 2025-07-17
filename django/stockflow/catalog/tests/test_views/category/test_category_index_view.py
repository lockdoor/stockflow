from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category
from catalog.views.category_views import CategoryIndexView


class CategoryIndexViewTest(TestCase):
    """
    Test CategoryIndexView - Focus on view behavior, permissions, template rendering, and context.
    """

    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpassword'
        )

        # Create some categories for testing
        self.category1 = Category.objects.create(
            name='Electronics',
            note='Electronics category',
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.category2 = Category.objects.create(
            name='Books',
            note='Books category',
            created_by=self.user,
            updated_by=self.user,
        )

    # =================================
    # AUTHENTICATION TESTS
    # =================================

    def test_index_view_requires_authentication(self):
        """Test that CategoryIndexView requires authentication"""
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_index_view_authenticated_user_can_access(self):
        """Test that authenticated user can access CategoryIndexView"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_index_view_different_user_can_access(self):
        """Test that different authenticated user can access CategoryIndexView"""
        self.client.login(username='otheruser', password='otherpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    # =================================
    # TEMPLATE TESTS
    # =================================

    def test_index_view_uses_correct_template(self):
        """Test that CategoryIndexView uses correct template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'catalog/category/category-index.html')

    def test_index_view_extends_base_template(self):
        """Test that CategoryIndexView template extends base template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Check that base template is used
        self.assertTemplateUsed(response, 'base.html')

    def test_index_view_includes_category_list_partial(self):
        """Test that CategoryIndexView includes category list partial"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Check that category list partial is included
        self.assertTemplateUsed(response, 'catalog/category/partials/category-list.html')

    # =================================
    # CONTEXT TESTS
    # =================================

    def test_index_view_context_contains_page_title(self):
        """Test that CategoryIndexView context contains page_title"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], 'Categories')

    def test_index_view_context_data_method(self):
        """Test that CategoryIndexView get_context_data method works correctly"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Check that standard context is available
        self.assertIn('view', response.context)
        self.assertIsInstance(response.context['view'], CategoryIndexView)

    # =================================
    # RESPONSE CONTENT TESTS
    # =================================

    def test_index_view_response_contains_page_title(self):
        """Test that CategoryIndexView response contains page title"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Check that page title is in the response
        self.assertContains(response, 'Categories')

    def test_index_view_response_contains_categories_content(self):
        """Test that CategoryIndexView response contains categories-related content"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Check that category-related content is in the response
        # (The actual categories are loaded via HTMX, so we check for structure)
        self.assertContains(response, 'category-list-htmx')
        self.assertContains(response, 'Loading categories...')

    def test_index_view_response_content_type(self):
        """Test that CategoryIndexView returns correct content type"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    # =================================
    # VIEW CLASS ATTRIBUTE TESTS
    # =================================

    def test_index_view_class_attributes(self):
        """Test that CategoryIndexView has correct class attributes"""
        # Check template_name
        self.assertEqual(
            CategoryIndexView.template_name,
            'catalog/category/category-index.html'
        )

    def test_index_view_inherits_from_correct_mixins(self):
        """Test that CategoryIndexView inherits from correct mixins"""
        # Check MRO (Method Resolution Order)
        mro = CategoryIndexView.__mro__
        mro_names = [cls.__name__ for cls in mro]
        
        # Should inherit from LoginRequiredMixin and TemplateView
        self.assertIn('LoginRequiredMixin', mro_names)
        self.assertIn('TemplateView', mro_names)

    # =================================
    # EDGE CASES AND ERROR HANDLING
    # =================================

    def test_index_view_with_no_categories(self):
        """Test CategoryIndexView when no categories exist"""
        # Delete all categories
        Category.objects.all().delete()
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Should still work without categories
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Categories')

    def test_index_view_with_many_categories(self):
        """Test CategoryIndexView with many categories"""
        # Create many categories
        for i in range(50):
            Category.objects.create(
                name=f'Category {i}',
                note=f'Category {i} description',
                created_by=self.user,
                updated_by=self.user,
            )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Should still work with many categories
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Categories')

    def test_index_view_with_inactive_categories(self):
        """Test CategoryIndexView with inactive categories"""
        # Create inactive category
        Category.objects.create(
            name='Inactive Category',
            note='This category is inactive',
            is_active=False,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Should work with inactive categories
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Categories')

    # =================================
    # HTTP METHOD TESTS
    # =================================

    def test_index_view_get_method(self):
        """Test CategoryIndexView GET method"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_index_view_post_method_not_allowed(self):
        """Test CategoryIndexView POST method is not allowed"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.post(url)
        
        # TemplateView doesn't allow POST by default
        self.assertEqual(response.status_code, 405)

    def test_index_view_head_method(self):
        """Test CategoryIndexView HEAD method"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.head(url)
        
        # HEAD should work for TemplateView
        self.assertEqual(response.status_code, 200)

    # =================================
    # URL REVERSE TESTS
    # =================================

    def test_index_view_url_reverse(self):
        """Test that CategoryIndexView URL can be reversed"""
        url = reverse('catalog:category-index')
        self.assertEqual(url, '/catalog/categories/')

    def test_index_view_url_name(self):
        """Test that CategoryIndexView URL name is correct"""
        url = reverse('catalog:category-index')
        self.assertIsNotNone(url)
        self.assertIn('categories', url)

    # =================================
    # INTEGRATION TESTS
    # =================================

    def test_index_view_integration_with_category_list(self):
        """Test CategoryIndexView integration with category list"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Should contain HTMX structure for category list loading
        self.assertContains(response, 'category-list-htmx')
        self.assertContains(response, 'hx-get="/catalog/categories/list/"')
        self.assertContains(response, 'Loading categories...')
        
        # Should include the category list partial
        self.assertTemplateUsed(response, 'catalog/category/partials/category-list.html')

    def test_index_view_context_available_in_template(self):
        """Test that CategoryIndexView context is available in template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        # Check that context variables are available
        self.assertIn('page_title', response.context)
        self.assertIn('view', response.context)
        
        # Check that template can access the context
        self.assertContains(response, 'Categories')  # page_title should be rendered

    # =================================
    # SECURITY TESTS
    # =================================

    def test_index_view_requires_login_mixin(self):
        """Test that CategoryIndexView properly uses LoginRequiredMixin"""
        # Without login should redirect
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_index_view_no_permission_required(self):
        """Test that CategoryIndexView doesn't require specific permissions"""
        # Should work with any authenticated user
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should work with different user too
        self.client.login(username='otheruser', password='otherpassword')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
