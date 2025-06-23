from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models.category import Category

class CategoriesViewTest(TestCase):
    """
    Test cases for the categories view.
    """

    def setUp(self):
        self.URL = '/catalog/categories'
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

    def test_view_requires_login(self):
        """
        Test that the categories view requires login.
        """
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)

    def test_categories_view(self):
        self.client.login(username='testuser', password='testpassword')
        """
        Test that the categories view returns a 200 status code.
        """
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/categories.html')

    def test_categories_has_link_to_create_category(self):
        """
        Test that the categories view has a link to create a new category.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertContains(response, 'href="/catalog/create_category?next=/catalog/categories"')

    def test_categories_should_has_zero_categories(self):
        """
        Test that the categories view should have zero categories.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertQuerySetEqual(response.context['categories'], [])

    def test_categories_should_has_one_category(self):
        category = Category.objects.create(
            name='Test Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertContains(response, category.name)
        self.assertQuerySetEqual(response.context['categories'], [category])

    def test_categories_should_has_one_category(self):
        category_1 = Category.objects.create(
            name='Test Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )
        category_2 = Category.objects.create(
            name='Another Category',
            description='This is another test category.',
            created_by=self.user,
            updated_by=self.user,
        )
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.URL)
        self.assertContains(response, category_1.name)
        self.assertContains(response, category_2.name)
        # check response context categories has two categories
        self.assertEqual(len(response.context['categories']), 2)
