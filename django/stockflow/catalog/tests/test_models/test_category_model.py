from django.test import TestCase
from catalog.models.category import Category
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
# from django.db import IntegrityError

class CategoryModelTest(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.category_exist =Category.objects.create(
            name='Test Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )
        self.category = Category(
            name='New Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_get_category(self):
        self.assertEqual(self.category_exist.name, 'Test Category')
        self.assertEqual(self.category_exist.description, 'This is a test category.')
        self.assertEqual(self.category_exist.created_by, self.user)
        self.assertEqual(self.category_exist.updated_by, self.user)
    
    def test_create_category(self):
        self.category.save()
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(self.category.name, 'New Category')
        self.assertEqual(self.category.description, 'This is a test category.')
        self.assertEqual(self.category.created_by, self.user)
        self.assertEqual(self.category.updated_by, self.user)
        
    def test_category_name_unique(self):
        self.category.name = 'Test Category'
        with self.assertRaises(ValidationError):
            self.category.full_clean()
    
    def test_category_name_not_empty(self):
        self.category.name = ''
        with self.assertRaises(ValidationError):
            self.category.full_clean()
            
    def test_category_name_not_null(self):
        self.category.name = None
        with self.assertRaises(ValidationError):
            self.category.full_clean()
            
    def test_category_name_length(self):
        self.category.name = 'a' * 101  # 101 characters long
        with self.assertRaises(ValidationError):
            self.category.full_clean()
            
    def test_update_category(self):
        self.category.save()
        self.category.name = 'Updated Category'
        self.category.save()
        updated_category = Category.objects.get(id=self.category.id)
        self.assertEqual(updated_category.name, 'Updated Category')
        
    def test_optimistic_locking(self):
        cat_1 = Category.objects.get(name="Test Category")
        self.assertEqual(cat_1.version, 0)
        cat_2 = Category.objects.get(name="Test Category")
        self.assertEqual(cat_2.version, 0)
        cat_1.save()
        self.assertEqual(cat_1.version, 1)
        with self.assertRaises(ValidationError) as e:
            cat_2.save()
        self.assertEqual("Optimistic Locking failed. The record has changed.", str(e.exception.message))
        
    def test_str_method(self):
        self.category.name = 'Test Category'
        self.assertEqual(str(self.category), 'Test Category')

    # Test for optional description field
    def test_category_description_optional(self):
        self.category.description = ''
        # with self.assertRaises(ValidationError):
        self.category.save()
        self.assertEqual(self.category.description, '')
        
        self.category.description = None
        self.category.save()
        self.assertEqual(self.category.description, '')
        
        # # Ensure it can be set to a non-empty string
        self.category.description = 'This is a new description.'
        self.category.save()
        self.assertEqual(self.category.description, 'This is a new description.')

        
    