from django.test import TestCase
from catalog.forms.category_form import CategoryForm
from catalog.models.category import Category
from django.contrib.auth.models import User

class CategoryFormTest(TestCase):

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
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        form_data = {
            'name': '',
            'description': 'This is a new category.'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_duplicate_category(self):
        form_data = {
            'name': 'Existing Category',
            'description': 'This is a duplicate category.'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
    def test_form_name_length_exceeds_limit(self):
        form_data = {
            'name': 'a' * 101,  # 101 characters long
            'description': 'This is a new category.'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
    def test_form_name_not_null(self):
        form_data = {
            'name': None,
            'description': 'This is a new category.'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
    def test_form_name_not_empty(self):
        form_data = {
            'name': '',
            'description': 'This is a new category.'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
    def test_form_description_default_value(self):
        form_data = {
            'name': 'Category with Default Description',
            'description': ''
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        category = form.save(commit=False)
        self.assertEqual(category.description, '')

    def test_form_save_creates_category(self):
        form_data = {
            'name': 'New Category',
            'description': 'This is a new category.'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        category = form.save(commit=False)
        category.created_by = self.user
        category.updated_by = self.user
        category.save()
        
        self.assertEqual(Category.objects.count(), 2)
        
        self.assertEqual(category.name, 'New Category')
        self.assertEqual(category.description, 'This is a new category.')
        self.assertEqual(category.created_by, self.user)
        self.assertEqual(category.updated_by, self.user)
        
    def test_form_save_updates_category(self):
        existing_category = Category.objects.get(name='Existing Category')
        form_data = {
            'name': 'Updated Category',
            'description': 'This is an updated category.'
        }
        form = CategoryForm(data=form_data, instance=existing_category)
        self.assertTrue(form.is_valid())
        updated_category = form.save(commit=False)
        updated_category.updated_by = self.user
        updated_category.save()
        
        existing_category.refresh_from_db()
        self.assertEqual(existing_category.name, 'Updated Category')
        self.assertEqual(existing_category.description, 'This is an updated category.')
        
        self.assertEqual(existing_category.updated_by, self.user)
        self.assertEqual(Category.objects.count(), 1)
        