from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models.category import Category
from catalog.views.category_views import CategoryListView


class CategoryListViewTest(TestCase):
    """
    Test CategoryListView - Focus on view behavior, permissions, and template rendering.
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

        # Create categories with different created_at times
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
        
        self.category3 = Category.objects.create(
            name='Clothing',
            note='Clothing category',
            created_by=self.other_user,
            updated_by=self.other_user,
        )

        # Create inactive category
        self.inactive_category = Category.objects.create(
            name='Inactive Category',
            note='This category is inactive',
            is_active=False,
            created_by=self.user,
            updated_by=self.user,
        )

    # =================================
    # AUTHENTICATION TESTS
    # =================================

    def test_list_view_requires_authentication(self):
        """Test that CategoryListView requires authentication"""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_list_view_authenticated_user_can_access(self):
        """Test that authenticated user can access CategoryListView"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    # =================================
    # TEMPLATE AND CONTEXT TESTS
    # =================================

    def test_list_view_uses_correct_template(self):
        """Test that CategoryListView uses correct template"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'catalog/category/partials/category-row.html')

    def test_list_view_context_object_name(self):
        """Test that CategoryListView uses correct context object name"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertIn('categories', response.context)
        self.assertIsNotNone(response.context['categories'])

    def test_list_view_contains_all_categories(self):
        """Test that CategoryListView contains all categories"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = response.context['categories']
        
        # Should contain all 4 categories (including inactive)
        self.assertEqual(len(categories), 4)
        
        # Check all categories are present
        category_names = [category.name for category in categories]
        self.assertIn('Electronics', category_names)
        self.assertIn('Books', category_names)
        self.assertIn('Clothing', category_names)
        self.assertIn('Inactive Category', category_names)

    def test_list_view_ordering(self):
        """Test that CategoryListView orders categories by -created_at"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = list(response.context['categories'])
        
        # Should be ordered by -created_at (newest first)
        for i in range(len(categories) - 1):
            self.assertGreaterEqual(
                categories[i].created_at,
                categories[i + 1].created_at
            )

    # =================================
    # QUERYSET TESTS
    # =================================

    def test_list_view_queryset_includes_inactive_categories(self):
        """Test that CategoryListView includes inactive categories"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = response.context['categories']
        inactive_categories = [cat for cat in categories if not cat.is_active]
        
        self.assertEqual(len(inactive_categories), 1)
        self.assertEqual(inactive_categories[0].name, 'Inactive Category')

    def test_list_view_queryset_includes_all_users_categories(self):
        """Test that CategoryListView includes categories from all users"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = response.context['categories']
        
        # Should include categories from both users
        created_by_users = [cat.created_by for cat in categories]
        self.assertIn(self.user, created_by_users)
        self.assertIn(self.other_user, created_by_users)

    # =================================
    # RESPONSE CONTENT TESTS
    # =================================

    def test_list_view_contains_category_names(self):
        """Test that CategoryListView response contains category names"""
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        content = response.content.decode('utf-8')
        
        # Should contain category names in the response
        self.assertIn('Electronics', content)
        self.assertIn('Books', content)
        self.assertIn('Clothing', content)

    def test_list_view_empty_queryset(self):
        """Test CategoryListView with empty queryset"""
        # Delete all categories
        Category.objects.all().delete()
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        categories = response.context['categories']
        self.assertEqual(len(categories), 0)

    # =================================
    # VIEW CLASS TESTS
    # =================================

    def test_view_class_attributes(self):
        """Test CategoryListView class attributes"""
        view = CategoryListView()
        
        self.assertEqual(view.model, Category)
        self.assertEqual(view.template_name, 'catalog/category/partials/category-list.html')
        self.assertEqual(view.context_object_name, 'categories')
        self.assertEqual(view.ordering, ['-created_at'])

    def test_view_class_mixins(self):
        """Test CategoryListView inherits from correct mixins"""
        from django.contrib.auth.mixins import LoginRequiredMixin
        from django.views.generic import ListView
        
        # Check that CategoryListView inherits from LoginRequiredMixin
        self.assertTrue(issubclass(CategoryListView, LoginRequiredMixin))
        self.assertTrue(issubclass(CategoryListView, ListView))

    # =================================
    # EDGE CASES TESTS
    # =================================

    def test_list_view_with_special_characters_in_category_name(self):
        """Test CategoryListView with special characters in category names"""
        special_category = Category.objects.create(
            name='Special & Characters!',
            note='Category with special characters',
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = response.context['categories']
        category_names = [cat.name for cat in categories]
        
        self.assertIn('Special & Characters!', category_names)

    def test_list_view_with_long_category_name(self):
        """Test CategoryListView with long category name"""
        long_name = 'A' * 99  # Close to max length (100)
        long_category = Category.objects.create(
            name=long_name,
            note='Category with long name',
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = response.context['categories']
        category_names = [cat.name for cat in categories]
        
        self.assertIn(long_name, category_names)

    def test_list_view_with_empty_note(self):
        """Test CategoryListView with categories that have empty notes"""
        empty_note_category = Category.objects.create(
            name='Empty Note Category',
            note='',
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.client.login(username='testuser', password='testpassword')
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        categories = response.context['categories']
        empty_note_categories = [cat for cat in categories if cat.note == '']
        
        self.assertEqual(len(empty_note_categories), 1)
        self.assertEqual(empty_note_categories[0].name, 'Empty Note Category')
