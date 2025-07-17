from django.test import TestCase
from django.core.exceptions import ValidationError
from django import forms
from catalog.forms.category_form import CategoryForm
from catalog.models.category import Category
from django.contrib.auth.models import User


class CategoryFormTest(TestCase):
    """
    Test CategoryForm - Focus on form validation and UI behavior only.
    Business logic (duplicate names, optimistic locking) should be tested in model tests.
    """

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

    # =================================
    # FORM VALIDATION TESTS
    # =================================

    def test_form_valid_data_create(self):
        """Test form with valid data for creating new category"""
        form_data = {
            'name': 'New Category',
            'note': 'This is a new category.'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'New Category')
        self.assertEqual(form.cleaned_data['note'], 'This is a new category.')

    def test_form_valid_data_minimal(self):
        """Test form with minimal valid data (name only)"""
        form_data = {
            'name': 'Minimal Category'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Minimal Category')
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_name_required(self):
        """Test that name field is required"""
        form_data = {
            'name': '',
            'note': 'Some note'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertEqual(form.errors['name'][0], 'This field is required.')

    def test_form_name_none(self):
        """Test that None name is invalid"""
        form_data = {
            'name': None,
            'note': 'Some note'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_name_whitespace_only(self):
        """Test that whitespace-only name is invalid"""
        form_data = {
            'name': '   ',
            'note': 'Some note'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertEqual(form.errors['name'][0], 'This field is required.')

    def test_form_name_stripped(self):
        """Test that name is stripped of whitespace (Django built-in behavior)"""
        form_data = {
            'name': '  Spaced Name  ',
            'note': 'Some note'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Spaced Name')

    def test_form_name_max_length(self):
        """Test name field max length validation"""
        form_data = {
            'name': 'a' * 101,  # 101 characters (max is 100)
            'note': 'Some note'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    # =================================
    # NOTE FIELD TESTS
    # =================================

    def test_form_note_optional(self):
        """Test that note field is optional"""
        form_data = {
            'name': 'Category Without Note'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_note_empty_string(self):
        """Test that empty note is valid"""
        form_data = {
            'name': 'Category With Empty Note',
            'note': ''
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_note_none(self):
        """Test that None note is converted to empty string"""
        form_data = {
            'name': 'Category With None Note',
            'note': None
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], '')

    def test_form_note_stripped(self):
        """Test that note is stripped of whitespace (Django built-in behavior)"""
        form_data = {
            'name': 'Category With Spaced Note',
            'note': '  This is a note with spaces  '
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], 'This is a note with spaces')

    # =================================
    # FORM SAVE TESTS
    # =================================

    def test_form_save_commit_false(self):
        """Test saving form with commit=False"""
        form_data = {
            'name': 'Uncommitted Category',
            'note': 'This category is not committed.'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        category = form.save(commit=False)
        self.assertEqual(category.name, 'Uncommitted Category')
        self.assertEqual(category.note, 'This category is not committed.')
        self.assertIsNone(category.pk)  # Should not be saved to database yet
        
        # Should be 0 categories in database
        self.assertEqual(Category.objects.count(), 0)

    def test_form_save_handles_model_error(self):
        """Test that form.save() handles errors from model and converts to ValidationError"""
        form_data = {
            'name': 'Test Category',
            'note': 'Test note'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Form save should raise ValidationError when model raises any error
        # This happens when required fields (created_by, updated_by) are missing
        # Could be ValueError from model business logic or IntegrityError from database
        with self.assertRaises(ValidationError):
            form.save()

    # =================================
    # WIDGET AND UI TESTS
    # =================================

    def test_form_widget_attributes(self):
        """Test that form widgets have correct attributes"""
        form = CategoryForm()
        
        # Check name field attributes
        name_widget = form.fields['name'].widget
        self.assertEqual(name_widget.attrs['placeholder'], 'Enter category name')
        self.assertEqual(name_widget.attrs['maxlength'], '100')
        
        # Check note field attributes
        note_widget = form.fields['note'].widget
        self.assertEqual(note_widget.attrs['placeholder'], 'Enter optional note')
        self.assertEqual(note_widget.attrs['rows'], 3)

    def test_form_labels(self):
        """Test that form fields have correct labels"""
        form = CategoryForm()
        
        self.assertEqual(form.fields['name'].label, 'Category Name')
        self.assertEqual(form.fields['note'].label, 'Note (Optional)')

    def test_form_field_types(self):
        """Test that form fields have correct types"""
        form = CategoryForm()
        
        self.assertIsInstance(form.fields['name'].widget, forms.TextInput)
        self.assertIsInstance(form.fields['note'].widget, forms.Textarea)

    def test_form_field_properties(self):
        """Test form field properties"""
        form = CategoryForm()
        
        # Name field should be required
        self.assertTrue(form.fields['name'].required)
        
        # Note field should be optional
        self.assertFalse(form.fields['note'].required)

    def test_form_meta_fields(self):
        """Test that form Meta includes correct fields"""
        form = CategoryForm()
        self.assertEqual(form.Meta.fields, ['name', 'note'])
        self.assertEqual(form.Meta.model, Category)
        