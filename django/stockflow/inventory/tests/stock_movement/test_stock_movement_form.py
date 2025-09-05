"""
Stock Movement Form Tests

Tests specifically for StockMovementForm including validation, normalization,
business rules, and widget configuration.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms

from inventory.forms import StockMovementForm
from inventory.models.warehouse import Warehouse
from inventory.models.stock_movement import StockMovement


class StockMovementFormTest(TestCase):
    """Test cases for StockMovementForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.active_warehouse = Warehouse.objects.create(
            name='Active Warehouse',
            code='ACTIVE01',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        # Create inactive warehouse by first creating active, then deactivating
        self.inactive_warehouse = Warehouse.objects.create(
            name='Inactive Warehouse',
            code='INACTIVE01',
            is_active=True,  # Create as active first
            created_by=self.user,
            updated_by=self.user
        )
        # Deactivate without validation to avoid circular dependency issues
        Warehouse.objects.filter(id=self.inactive_warehouse.id).update(is_active=False)
    
    def test_form_fields_present(self):
        """Test that form contains all expected fields"""
        form = StockMovementForm()
        expected_fields = ['reference_type', 'reference_id', 'note', 'warehouse']
        
        for field_name in expected_fields:
            self.assertIn(field_name, form.fields)
        
        # Ensure status field is NOT present (it's managed by model)
        self.assertNotIn('status', form.fields)
    
    def test_form_labels(self):
        """Test that form has correct field labels"""
        form = StockMovementForm()
        expected_labels = {
            'reference_type': 'Reference Type',
            'reference_id': 'Reference ID',
            'note': 'Notes',
            'warehouse': 'Warehouse',
        }
        
        for field_name, expected_label in expected_labels.items():
            self.assertEqual(form.fields[field_name].label, expected_label)
    
    def test_form_help_texts(self):
        """Test that form has informative help texts"""
        form = StockMovementForm()
        
        # Check that help texts exist and are meaningful
        self.assertIsNotNone(form.fields['reference_type'].help_text)
        self.assertIsNotNone(form.fields['reference_id'].help_text)
        self.assertIsNotNone(form.fields['note'].help_text)
        self.assertIsNotNone(form.fields['warehouse'].help_text)
        
        # Check specific help text content
        self.assertIn('type of document', form.fields['reference_type'].help_text.lower())
        self.assertIn('referenced document', form.fields['reference_id'].help_text.lower())
    
    def test_form_widgets(self):
        """Test that form widgets have correct attributes"""
        form = StockMovementForm()
        
        # Test CSS classes
        self.assertIn('form-select', form.fields['reference_type'].widget.attrs.get('class', ''))
        self.assertIn('form-control', form.fields['reference_id'].widget.attrs.get('class', ''))
        self.assertIn('form-control', form.fields['note'].widget.attrs.get('class', ''))
        self.assertIn('form-select', form.fields['warehouse'].widget.attrs.get('class', ''))
        
        # Test specific widget attributes
        self.assertEqual(form.fields['reference_id'].widget.attrs.get('min'), '1')
        self.assertEqual(form.fields['note'].widget.attrs.get('rows'), 3)
        self.assertEqual(form.fields['note'].widget.attrs.get('maxlength'), '1000')
        
        # Test placeholders
        self.assertIn('reference id', form.fields['reference_id'].widget.attrs.get('placeholder', '').lower())
        self.assertIn('notes', form.fields['note'].widget.attrs.get('placeholder', '').lower())
    
    def test_warehouse_queryset_active_only(self):
        """Test that warehouse field only shows active warehouses"""
        form = StockMovementForm()
        warehouse_queryset = form.fields['warehouse'].queryset
        
        # Should include active warehouse
        self.assertIn(self.active_warehouse, warehouse_queryset)
        # Should NOT include inactive warehouse
        self.assertNotIn(self.inactive_warehouse, warehouse_queryset)
        
        # Verify queryset filters correctly
        self.assertTrue(all(warehouse.is_active for warehouse in warehouse_queryset))
    
    def test_initial_values_new_form(self):
        """Test initial values for new form instance"""
        form = StockMovementForm()
        
        # Reference type should default to NONE
        self.assertEqual(form.fields['reference_type'].initial, StockMovement.ReferenceType.NONE)
        
        # Reference ID should not be required
        self.assertFalse(form.fields['reference_id'].required)


class StockMovementFormValidationTest(TestCase):
    """Test validation logic for StockMovementForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_valid_form_with_none_reference(self):
        """Test valid form submission with NONE reference type"""
        form_data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': 'Test movement with no reference',
        }
        form = StockMovementForm(data=form_data)
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Verify cleaned data
        self.assertEqual(form.cleaned_data['reference_type'], StockMovement.ReferenceType.NONE)
        self.assertEqual(form.cleaned_data['warehouse'], self.warehouse)
        self.assertEqual(form.cleaned_data['note'], 'Test movement with no reference')
        self.assertIsNone(form.cleaned_data.get('reference_id'))
    
    def test_valid_form_with_reference_id(self):
        """Test valid form with reference type that requires ID"""
        test_cases = [
            StockMovement.ReferenceType.PRODUCTION,
            StockMovement.ReferenceType.ADJUST,
        ]
        
        for ref_type in test_cases:
            with self.subTest(reference_type=ref_type):
                form_data = {
                    'reference_type': ref_type,
                    'reference_id': 12345,
                    'warehouse': self.warehouse.id,
                    'note': f'Test movement for {ref_type}',
                }
                form = StockMovementForm(data=form_data)
                
                self.assertTrue(form.is_valid(), f"Form should be valid for {ref_type}. Errors: {form.errors}")
                self.assertEqual(form.cleaned_data['reference_type'], ref_type)
                self.assertEqual(form.cleaned_data['reference_id'], 12345)
    
    def test_reference_id_required_validation(self):
        """Test that reference_id is required for non-NONE reference types"""
        required_ref_types = [
            StockMovement.ReferenceType.PRODUCTION,
            StockMovement.ReferenceType.ADJUST,
        ]
        
        for ref_type in required_ref_types:
            with self.subTest(reference_type=ref_type):
                form_data = {
                    'reference_type': ref_type,
                    'warehouse': self.warehouse.id,
                    # reference_id is missing
                }
                form = StockMovementForm(data=form_data)
                
                self.assertFalse(form.is_valid(), f"Form should be invalid for {ref_type} without reference_id")
                # Model validation puts errors in __all__ (non-field errors)
                self.assertIn('__all__', form.errors)
                self.assertIn(f'Reference ID is required when reference type is {ref_type}', 
                            str(form.errors['__all__']))
    
    def test_reference_id_optional_for_none_type(self):
        """Test that reference_id is optional for NONE reference type"""
        # Test without reference_id - should be valid
        form_data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
        }
        form = StockMovementForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        self.assertIsNone(form.cleaned_data.get('reference_id'))
        
        # Test with reference_id - model validation should catch this  
        form_data['reference_id'] = 999
        form = StockMovementForm(data=form_data)
        self.assertFalse(form.is_valid(), f"Form should be invalid when reference_id provided with NONE type")
        # Model validation puts this error in __all__
        self.assertIn('__all__', form.errors)
        self.assertIn('Reference ID must be empty when reference type is None', str(form.errors['__all__']))
    
    def test_required_fields_validation(self):
        """Test validation of required fields"""
        # Test empty form
        form = StockMovementForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('reference_type', form.errors)
        self.assertIn('warehouse', form.errors)
        
        # Test missing warehouse
        form_data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'note': 'Test note',
        }
        form = StockMovementForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('warehouse', form.errors)
        
        # Test missing reference_type
        form_data = {
            'warehouse': self.warehouse.id,
            'note': 'Test note',
        }
        form = StockMovementForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('reference_type', form.errors)
    
    def test_invalid_reference_id_values(self):
        """Test validation of invalid reference_id values"""
        invalid_values = [0, -1, -999, 'invalid', '']
        
        for invalid_value in invalid_values:
            with self.subTest(reference_id=invalid_value):
                form_data = {
                    'reference_type': StockMovement.ReferenceType.PRODUCTION,
                    'reference_id': invalid_value,
                    'warehouse': self.warehouse.id,
                }
                form = StockMovementForm(data=form_data)
                
                if invalid_value == '' or invalid_value == 'invalid':
                    # Should fail due to custom validation
                    self.assertFalse(form.is_valid())
                elif invalid_value <= 0:
                    # Should fail due to min value constraint
                    self.assertFalse(form.is_valid())


class StockMovementFormCleaningTest(TestCase):
    """Test data cleaning and normalization in StockMovementForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TEST01',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_note_cleaning_whitespace(self):
        """Test that note field handles whitespace correctly"""
        test_cases = [
            ('Normal note', 'Normal note'),
            ('  Note with spaces  ', 'Note with spaces'),
            ('\tNote with tabs\t', 'Note with tabs'),
            ('\nNote with newlines\n', 'Note with newlines'),
            ('  \t\n  ', None),  # Only whitespace becomes None
            ('', None),  # Empty string becomes None
        ]
        
        for input_note, expected_note in test_cases:
            with self.subTest(input_note=repr(input_note)):
                form_data = {
                    'reference_type': StockMovement.ReferenceType.NONE,
                    'warehouse': self.warehouse.id,
                    'note': input_note,
                }
                form = StockMovementForm(data=form_data)
                
                self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
                self.assertEqual(form.cleaned_data['note'], expected_note)
    
    def test_note_multiline_handling(self):
        """Test that multiline notes are preserved"""
        multiline_note = "Line 1\nLine 2\nLine 3"
        form_data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': multiline_note,
        }
        form = StockMovementForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], multiline_note)
    
    def test_note_length_boundaries(self):
        """Test note field length handling"""
        # Test max length (1000 characters)
        max_length_note = 'x' * 1000
        form_data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
            'note': max_length_note,
        }
        form = StockMovementForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Note: Django forms don't automatically enforce widget maxlength,
        # but the widget should have maxlength attribute for client-side validation
        self.assertEqual(form.fields['note'].widget.attrs.get('maxlength'), '1000')


class StockMovementFormIntegrationTest(TestCase):
    """Integration tests for StockMovementForm with model creation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.warehouse = Warehouse.objects.create(
            name='Integration Test Warehouse',
            code='INTEG01',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_form_save_creates_model_instance(self):
        """Test that valid form can create StockMovement model instance"""
        form_data = {
            'reference_type': StockMovement.ReferenceType.ADJUST,
            'reference_id': 555,
            'warehouse': self.warehouse.id,
            'note': 'Integration test movement',
        }
        form = StockMovementForm(data=form_data)
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Save form data to model
        instance = form.save(commit=False)
        instance.created_by = self.user
        instance.updated_by = self.user
        instance.save()
        
        # Verify model instance
        self.assertEqual(instance.reference_type, StockMovement.ReferenceType.ADJUST)
        self.assertEqual(instance.reference_id, 555)
        self.assertEqual(instance.warehouse, self.warehouse)
        self.assertEqual(instance.note, 'Integration test movement')
        self.assertEqual(instance.status, StockMovement.Status.DRAFT)  # Default status
        self.assertEqual(instance.created_by, self.user)
        self.assertEqual(instance.updated_by, self.user)
        
        # Verify it's saved to database
        saved_instance = StockMovement.objects.get(id=instance.id)
        self.assertEqual(saved_instance.reference_type, StockMovement.ReferenceType.ADJUST)
        self.assertEqual(saved_instance.warehouse, self.warehouse)
    
    def test_form_edit_existing_instance(self):
        """Test that form can edit existing StockMovement instance"""
        # Create existing instance
        existing_movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.NONE,
            warehouse=self.warehouse,
            note='Original note',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Edit with form
        form_data = {
            'reference_type': StockMovement.ReferenceType.PRODUCTION,
            'reference_id': 777,
            'warehouse': self.warehouse.id,
            'note': 'Updated note',
        }
        form = StockMovementForm(data=form_data, instance=existing_movement)
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Save updated data
        updated_instance = form.save(commit=False)
        updated_instance.updated_by = self.user
        updated_instance.save()
        
        # Verify updates
        updated_instance.refresh_from_db()
        self.assertEqual(updated_instance.reference_type, StockMovement.ReferenceType.PRODUCTION)
        self.assertEqual(updated_instance.reference_id, 777)
        self.assertEqual(updated_instance.note, 'Updated note')
        self.assertEqual(updated_instance.warehouse, self.warehouse)
        
        # Original fields should remain
        self.assertEqual(updated_instance.created_by, self.user)
        self.assertEqual(updated_instance.status, StockMovement.Status.DRAFT)
    
    def test_form_validation_with_business_rules(self):
        """Test form validation respects business rules from model"""
        # This test focuses on form-level validation, not deep model validation
        # since we want to test the form's ability to catch issues before model save
        
        # Test with missing required data for business rules
        form_data = {
            'reference_type': StockMovement.ReferenceType.PRODUCTION,
            'warehouse': self.warehouse.id,
            'note': 'Test note',
            # Missing reference_id for PRODUCTION type
        }
        form = StockMovementForm(data=form_data)
        
        # Model validation should catch this  
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Reference ID is required when reference type is PRODUCTION', str(form.errors['__all__']))
    
    def test_form_preserves_model_defaults(self):
        """Test that form doesn't interfere with model defaults"""
        form_data = {
            'reference_type': StockMovement.ReferenceType.NONE,
            'warehouse': self.warehouse.id,
        }
        form = StockMovementForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        instance = form.save(commit=False)
        instance.created_by = self.user
        instance.updated_by = self.user
        instance.save()
        
        # Model defaults should be preserved
        self.assertEqual(instance.status, StockMovement.Status.DRAFT)
        self.assertIsNotNone(instance.created_at)
        self.assertIsNotNone(instance.updated_at)
        self.assertEqual(instance.version, 1)  # From AuditableMixin


class StockMovementFormAccessibilityTest(TestCase):
    """Test accessibility and usability features of StockMovementForm"""
    
    def test_form_has_proper_labels(self):
        """Test that all fields have proper labels for accessibility"""
        form = StockMovementForm()
        
        for field_name, field in form.fields.items():
            with self.subTest(field=field_name):
                self.assertIsNotNone(field.label, f"Field {field_name} should have a label")
                self.assertTrue(len(field.label) > 0, f"Field {field_name} label should not be empty")
    
    def test_form_has_help_texts(self):
        """Test that fields have helpful descriptions"""
        form = StockMovementForm()
        
        for field_name, field in form.fields.items():
            with self.subTest(field=field_name):
                self.assertIsNotNone(field.help_text, f"Field {field_name} should have help text")
                self.assertTrue(len(field.help_text) > 10, f"Field {field_name} help text should be descriptive")
    
    def test_form_widget_accessibility_attributes(self):
        """Test that widgets have accessibility-friendly attributes"""
        form = StockMovementForm()
        
        # Check that number input has proper attributes
        ref_id_widget = form.fields['reference_id'].widget
        self.assertEqual(ref_id_widget.attrs.get('min'), '1')
        self.assertIn('placeholder', ref_id_widget.attrs)
        
        # Check that textarea has proper sizing
        note_widget = form.fields['note'].widget
        self.assertIn('rows', note_widget.attrs)
        self.assertIn('placeholder', note_widget.attrs)
        
        # Check that selects have proper classes
        for select_field in ['reference_type', 'warehouse']:
            widget = form.fields[select_field].widget
            self.assertIn('form-select', widget.attrs.get('class', ''))
    
    def test_form_error_messages_are_helpful(self):
        """Test that form produces helpful error messages"""
        # Test with invalid data to trigger various error messages
        form_data = {
            'reference_type': StockMovement.ReferenceType.PRODUCTION,
            'warehouse': '',  # Invalid
            'reference_id': '',  # Missing for PRODUCTION type
        }
        form = StockMovementForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        
        # Check that error messages are helpful
        if 'warehouse' in form.errors:
            warehouse_error = str(form.errors['warehouse'])
            self.assertIn('required', warehouse_error.lower())
        
        if 'reference_id' in form.errors:
            ref_id_error = str(form.errors['reference_id'])
            self.assertIn('required', ref_id_error.lower())
            self.assertIn('PRODUCTION', ref_id_error)  # Should mention the reference type
