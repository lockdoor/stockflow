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
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword2'
        )
        
        self.category_exist = Category.objects.create(
            name='Test Category',
            note='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_category_success(self):
        """Test creating a category successfully"""
        category = Category(
            name='New Category',
            note='This is a new category.',
            created_by=self.user,
            updated_by=self.user,
        )
        category.save()
        
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(category.name, 'New Category')
        self.assertEqual(category.note, 'This is a new category.')
        self.assertEqual(category.created_by, self.user)
        self.assertEqual(category.updated_by, self.user)
        self.assertTrue(category.is_active)
        self.assertEqual(category.version, 0)

    def test_create_category_name_strip(self):
        """Test that category name is stripped on save"""
        category = Category(
            name='  Spaces Category  ',
            created_by=self.user,
            updated_by=self.user,
        )
        category.save()
        
        self.assertEqual(category.name, 'Spaces Category')

    def test_create_category_empty_name_raises_error(self):
        """Test that empty name raises ValueError"""
        category = Category(
            name='',
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValueError) as context:
            category.save()
        self.assertEqual(str(context.exception), "Category name cannot be empty.")

    def test_create_category_whitespace_name_raises_error(self):
        """Test that whitespace-only name raises ValueError"""
        category = Category(
            name='   ',
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValueError) as context:
            category.save()
        self.assertEqual(str(context.exception), "Category name cannot be empty.")

    def test_create_category_duplicate_name_raises_error(self):
        """Test that duplicate name raises ValueError"""
        category = Category(
            name='Test Category',  # Same as existing
            created_by=self.user,
            updated_by=self.user,
        )
        
        with self.assertRaises(ValueError) as context:
            category.save()
        self.assertEqual(str(context.exception), "Category with name 'Test Category' already exists.")

    def test_update_category_duplicate_name_raises_error(self):
        """Test that updating to duplicate name raises ValueError"""
        # Create another category
        category2 = Category.objects.create(
            name='Another Category',
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Try to update to existing name
        category2.name = 'Test Category'  # Same as existing
        
        with self.assertRaises(ValueError) as context:
            category2.save()
        self.assertEqual(str(context.exception), "Category with name 'Test Category' already exists.")

    def test_update_category_success(self):
        """Test updating a category successfully"""
        original_version = self.category_exist.version
        self.category_exist.name = 'Updated Category'
        self.category_exist.note = 'Updated note'
        self.category_exist.updated_by = self.user2
        self.category_exist.save()
        
        updated_category = Category.objects.get(id=self.category_exist.id)
        self.assertEqual(updated_category.name, 'Updated Category')
        self.assertEqual(updated_category.note, 'Updated note')
        self.assertEqual(updated_category.updated_by, self.user2)
        self.assertEqual(updated_category.version, original_version + 1)

    def test_optimistic_locking_success(self):
        """Test optimistic locking works correctly"""
        cat_1 = Category.objects.get(name="Test Category")
        cat_2 = Category.objects.get(name="Test Category")
        
        # Both should have same version initially
        self.assertEqual(cat_1.version, 0)
        self.assertEqual(cat_2.version, 0)
        
        # First save should succeed and increment version
        cat_1.name = "Updated by Cat 1"
        cat_1.save()
        self.assertEqual(cat_1.version, 1)
        
        # Second save should fail due to version mismatch
        cat_2.name = "Updated by Cat 2"
        with self.assertRaises(ValueError) as context:
            cat_2.save()
        self.assertEqual(str(context.exception), "Optimistic Locking failed. The record has changed.")

    def test_delete_category_optimistic_locking(self):
        """Test optimistic locking when category is deleted"""
        cat_1 = Category.objects.get(name="Test Category")
        cat_id = cat_1.id
        
        # Delete the category
        cat_1.delete()
        
        # Try to save a stale reference
        stale_cat = Category(id=cat_id, name="Stale", created_by=self.user, updated_by=self.user, version=0)
        stale_cat.pk = cat_id
        
        with self.assertRaises(ValueError) as context:
            stale_cat.save()
        self.assertEqual(str(context.exception), "Category no longer exists.")

    def test_get_active_classmethod(self):
        """Test get_active class method"""
        # Create inactive category
        inactive_cat = Category.objects.create(
            name='Inactive Category',
            note='This is inactive',
            is_active=False,
            created_by=self.user,
            updated_by=self.user,
        )
        
        active_categories = Category.get_active()
        self.assertEqual(active_categories.count(), 1)
        self.assertEqual(active_categories.first().name, 'Test Category')
        
        # Test that inactive category is not included
        all_categories = Category.objects.all()
        self.assertEqual(all_categories.count(), 2)

    def test_deactivate_method(self):
        """Test deactivate method"""
        self.assertTrue(self.category_exist.is_active)
        
        self.category_exist.deactivate()
        
        self.assertFalse(self.category_exist.is_active)
        # Verify it's saved in database
        reloaded = Category.objects.get(id=self.category_exist.id)
        self.assertFalse(reloaded.is_active)

    def test_activate_method(self):
        """Test activate method"""
        # First deactivate
        self.category_exist.is_active = False
        self.category_exist.save()
        
        self.category_exist.activate()
        
        self.assertTrue(self.category_exist.is_active)
        # Verify it's saved in database
        reloaded = Category.objects.get(id=self.category_exist.id)
        self.assertTrue(reloaded.is_active)

    def test_str_method(self):
        """Test string representation"""
        self.assertEqual(str(self.category_exist), 'Test Category')

    def test_note_field_optional(self):
        """Test note field is optional"""
        category = Category(
            name='No Note Category',
            created_by=self.user,
            updated_by=self.user,
        )
        category.save()
        
        self.assertEqual(category.note, '')

    def test_note_field_can_be_set(self):
        """Test note field can be set and updated"""
        category = Category(
            name='With Note Category',
            note='Original note',
            created_by=self.user,
            updated_by=self.user,
        )
        category.save()
        
        self.assertEqual(category.note, 'Original note')
        
        # Update note
        category.note = 'Updated note'
        category.save()
        
        reloaded = Category.objects.get(id=category.id)
        self.assertEqual(reloaded.note, 'Updated note')

    def test_default_values(self):
        """Test default field values"""
        category = Category(
            name='Default Values Category',
            created_by=self.user,
            updated_by=self.user,
        )
        category.save()
        
        self.assertEqual(category.note, '')
        self.assertTrue(category.is_active)
        self.assertEqual(category.version, 0)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

    def test_meta_ordering(self):
        """Test Meta ordering by name"""
        Category.objects.create(
            name='A Category',
            created_by=self.user,
            updated_by=self.user,
        )
        Category.objects.create(
            name='Z Category',
            created_by=self.user,
            updated_by=self.user,
        )
        
        categories = Category.objects.all()
        names = [cat.name for cat in categories]
        
        # Should be ordered by name
        self.assertEqual(names, ['A Category', 'Test Category', 'Z Category'])

    def test_history_tracking(self):
        """Test that history is tracked"""
        # Update category
        self.category_exist.name = 'Updated Name'
        self.category_exist.save()
        
        # Check history exists
        history = self.category_exist.history.all()
        self.assertEqual(history.count(), 2)  # Create + Update
        
        # Check history contains both versions
        history_names = [h.name for h in history]
        self.assertIn('Test Category', history_names)
        self.assertIn('Updated Name', history_names)

        
    