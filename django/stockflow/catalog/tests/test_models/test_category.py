from django.test import TestCase
from catalog.models.category import Category
from django.contrib.auth.models import User

class CategoryModelTest(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        Category.objects.create(
            name='Test Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_category_creation(self):
        category = Category.objects.get(name='Test Category')
        self.assertEqual(category.description, 'This is a test category.')

    def test_str_representation(self):
        category = Category.objects.get(name='Test Category')
        self.assertEqual(str(category), 'Test Category')

    def test_unique_name(self):
        with self.assertRaises(Exception):
            Category.objects.create(
                name='Test Category',
                description='Duplicate category.'
            )
