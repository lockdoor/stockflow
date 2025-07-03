from django.test import TestCase
from catalog.forms.item_form import ItemForm
from django import forms
from catalog.models.category import Category
from django.contrib.auth.models import User

class ItemFormTest(TestCase):
    def setUp(self):
        # Create new user for make category
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        # Create a category first
        self.category = Category.objects.create(
            name='Existing Category',
            created_by=self.user,
            updated_by=self.user
            )
        
        self.form_data = {
            'sku_code': 'RAW001',
            'name': 'Raw Material 1',
            'unit': 'kg',
            'type': 'RAW',  # Assuming 'RAW' is a valid type
            'status': 'ACTIVE',
            'description': 'This is a test raw material.',
            'category': self.category.id  # Use existing category
        }

    def test_form_fields(self):
        form = ItemForm()
        self.assertIn('sku_code', form.fields)
        self.assertIn('name', form.fields)
        self.assertIn('unit', form.fields)
        self.assertIn('status', form.fields)
        self.assertIn('description', form.fields)

    def test_form_field_types(self):
        form = ItemForm()
        self.assertIsInstance(form.fields['sku_code'], forms.CharField)
        self.assertIsInstance(form.fields['name'], forms.CharField)
        self.assertIsInstance(form.fields['unit'], forms.CharField)
        self.assertIsInstance(form.fields['status'], forms.ChoiceField)
        self.assertIsInstance(form.fields['description'], forms.CharField)
    
    def test_form_widget_classes(self):
        form = ItemForm()
        self.assertEqual(form.fields['sku_code'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['name'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['unit'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['status'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['description'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['description'].widget.attrs['rows'], 3)

    def test_form_valid_data(self):
        form = ItemForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data_sku(self):
        self.form_data['sku_code'] = ''  # Empty SKU code
        form = ItemForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('sku_code', form.errors)

    def test_form_invalid_data_status(self):
        self.form_data['status'] = 'INVALID_STATUS'  # Invalid status
        form = ItemForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
    
    def test_form_empty_data(self):
        form = ItemForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('sku_code', form.errors)
        self.assertIn('name', form.errors)
        self.assertIn('unit', form.errors)
        self.assertIn('status', form.errors)
        self.assertIn('type', form.errors)
        self.assertEqual(len(form.errors), 5)
    
    def test_form_required_fields(self):
        form = ItemForm()
        self.assertTrue(form.fields['sku_code'].required)
        self.assertTrue(form.fields['name'].required)
        self.assertTrue(form.fields['unit'].required)
        self.assertTrue(form.fields['status'].required)

    def test_form_optional_fields(self):
        form = ItemForm()
        self.assertFalse(form.fields['description'].required)
        self.assertFalse(form.fields['description'].initial)

    def test_form_initial_values(self):
        form = ItemForm()
        self.assertEqual(form.fields['status'].initial, 'ACTIVE')

    def test_form_null_category(self):
        self.form_data['category'] = None  # No category selected
        form = ItemForm(data=self.form_data)
        self.assertTrue(form.is_valid())


    def test_form_invalid_category_1(self):
        form_data = {
            'sku_code': 'RAW004',
            'name': 'Raw Material 4',
            'unit': 'm',
            'status': 'ACTIVE',
            'description': 'This is a test raw material with invalid category.',
            'category': 9999  # Non-existent category ID
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_form_invalid_category_2(self):
        form_data = {
            'sku_code': 'RAW004',
            'name': 'Raw Material 4',
            'unit': 'm',
            'status': 'ACTIVE',
            'description': 'This is a test raw material with invalid category.',
            'category': 'A'  # Invalid category value
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_category_field_selection_has_one_item(self):
        form = ItemForm()
        self.assertIsInstance(form.fields['category'], forms.ModelChoiceField)
        self.assertEqual(form.fields['category'].queryset.count(), 1)
        self.assertEqual(form.fields['category'].queryset.first(), self.category)

    
    def test_category_field_selection_has_no_items(self):
        Category.objects.all().delete()
        form = ItemForm()
        self.assertIsInstance(form.fields['category'], forms.ModelChoiceField)
        self.assertEqual(form.fields['category'].queryset.count(), 0)
