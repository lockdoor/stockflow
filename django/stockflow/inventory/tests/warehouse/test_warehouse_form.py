"""
Test Warehouse Form

Tests for the simplified Warehouse form that focuses on basic form validation
while delegating business logic to the model layer.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from inventory.models.warehouse import Warehouse
from inventory.forms.warehouse_form import WarehouseForm


class WarehouseFormTest(TestCase):
    """Test case for Warehouse form"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_valid_form_with_all_fields(self):
        """Test form with all valid fields"""
        data = {
            'name': 'Test Warehouse',
            'code': 'TEST01',
            'address': '123 Test Avenue',
            'note': 'Test warehouse note',
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Check code normalization
        self.assertEqual(form.cleaned_data['code'], 'TEST01')

    def test_valid_form_minimal_fields(self):
        """Test form with only required fields"""
        data = {
            'name': 'Minimal Warehouse',
            'code': 'MIN01',
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_form_field_labels(self):
        """Test that form field labels are correct"""
        form = WarehouseForm()
        self.assertEqual(form.fields['name'].label, 'Warehouse Name')
        self.assertEqual(form.fields['code'].label, 'Warehouse Code')
        self.assertEqual(form.fields['address'].label, 'Address')
        self.assertEqual(form.fields['note'].label, 'Notes')
        self.assertEqual(form.fields['is_active'].label, 'Active Status')

    def test_form_initial_values_new_instance(self):
        """Test initial values for new warehouse"""
        form = WarehouseForm()
        self.assertTrue(form.fields['is_active'].initial)

    def test_code_normalization(self):
        """Test that code is normalized to uppercase"""
        data = {
            'name': 'Test Warehouse',
            'code': 'test01',  # lowercase
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['code'], 'TEST01')

    def test_code_normalization_with_spaces(self):
        """Test that code strips whitespace and normalizes"""
        data = {
            'name': 'Test Warehouse',
            'code': '  test01  ',  # with spaces
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['code'], 'TEST01')

    def test_form_widget_attributes(self):
        """Test that form widgets have correct attributes"""
        form = WarehouseForm()
        
        # Test code field has uppercase transform
        code_widget = form.fields['code'].widget
        self.assertIn('text-transform: uppercase', code_widget.attrs.get('style', ''))
        self.assertIn('oninput', code_widget.attrs)
        
        # Test placeholders are set
        self.assertIn('placeholder', form.fields['name'].widget.attrs)
        self.assertIn('placeholder', form.fields['code'].widget.attrs)
        self.assertIn('placeholder', form.fields['address'].widget.attrs)
        self.assertIn('placeholder', form.fields['note'].widget.attrs)

    def test_form_help_texts(self):
        """Test that help texts are informative"""
        form = WarehouseForm()
        self.assertIn('2-100 characters', form.fields['name'].help_text)
        self.assertIn('2-10 alphanumeric', form.fields['code'].help_text)
        self.assertIn('optional', form.fields['address'].help_text)
        self.assertIn('optional', form.fields['note'].help_text)

    def test_name_validation_too_short(self):
        """Test name validation with too short name"""
        data = {
            'name': 'A',  # Too short
            'code': 'TEST01',
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertFalse(form.is_valid())
        # Error might be in __all__ or name field due to model validation
        form_errors_str = str(form.errors)
        self.assertIn('at least 2 characters', form_errors_str)

    def test_duplicate_code_validation(self):
        """Test validation for duplicate warehouse codes"""
        # Create existing warehouse with super save to bypass validation
        existing = Warehouse(
            name='Existing Warehouse',
            code='EXIST01',
            created_by=self.user,
            updated_by=self.user
        )
        # Use super save to bypass custom save logic in tests
        super(Warehouse, existing).save()
        
        # Try to create another with same code
        data = {
            'name': 'New Warehouse',
            'code': 'EXIST01',  # Same code
            'is_active': True,
        }
        form = WarehouseForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)
        self.assertIn('already exists', str(form.errors['code']))

    def test_form_editing_existing_warehouse(self):
        """Test form when editing existing warehouse"""
        # Create existing warehouse using super save to bypass validation
        warehouse = Warehouse(
            name='Original Warehouse',
            code='ORIG01',
            created_by=self.user,
            updated_by=self.user
        )
        super(Warehouse, warehouse).save()
        
        # Edit with form
        data = {
            'name': 'Updated Warehouse',
            'code': 'ORIG01',  # Same code (should be allowed)
            'address': 'Updated address',
            'is_active': False,
        }
        form = WarehouseForm(data=data, instance=warehouse)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        updated_warehouse = form.save(commit=False)
        updated_warehouse.updated_by = self.user
        updated_warehouse.save()
        
        self.assertEqual(updated_warehouse.name, 'Updated Warehouse')
        self.assertEqual(updated_warehouse.code, 'ORIG01')
        self.assertFalse(updated_warehouse.is_active)

    def test_default_active_status_for_new_warehouse(self):
        """Test that new warehouses default to active"""
        form = WarehouseForm()
        self.assertTrue(form.fields['is_active'].initial)
        
        # Check maxlength attributes
        self.assertEqual(form.fields['name'].widget.attrs['maxlength'], '100')
        self.assertEqual(form.fields['code'].widget.attrs['maxlength'], '10')
