from django.test import TestCase
from catalog.forms.create_category_form import CreateCategoryForm
from catalog.models.category import Category
from django.contrib.auth.models import User

class CreateCategoryFormTest(TestCase):

    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        # Create an initial category to test uniqueness
        self.category = Category.objects.create(
            name='Existing Category',
            description='This is an existing category.',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_form_valid_data(self):
        form_data = {
            'name': 'New Category',
            'description': 'This is a new category.'
        }
        form = CreateCategoryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        form_data = {
            'name': '',
            'description': 'This is a new category.'
        }
        form = CreateCategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_duplicate_category(self):
        form_data = {
            'name': 'Existing Category',
            'description': 'This is a duplicate category.'
        }
        form = CreateCategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
