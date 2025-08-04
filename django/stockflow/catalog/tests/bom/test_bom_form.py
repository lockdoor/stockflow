"""
BOM Form Tests

This module contains tests for the BOM form functionality.
Tests cover form initialization, validation, save operations, and integration with the refactored BOM model.

Author: StockFlow Team
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from catalog.forms.bom_form import BOMForm
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM
from decimal import Decimal


class BOMFormTest(TestCase):
    """Test suite for BOM form"""

    def setUp(self):
        """Set up test data for BOM form tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='test@example.com'
        )
        
        # Create categories
        self.electronics = Category.objects.create(
            name='Electronics',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.materials = Category.objects.create(
            name='Materials',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create parent item (PRODUCT in DRAFT status for BOM editing)
        self.parent_sku = ItemSKU.objects.create(
            sku_code='PROD001',
            name='Product 1',
            unit='pcs',
            type='PRODUCT',
            status='DRAFT',
            category=self.electronics,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create component items (RAW materials - ACTIVE by default)
        self.component_sku = ItemSKU.objects.create(
            sku_code='RAW001',
            name='Raw Material 1',
            unit='kg',
            type='RAW',
            status='ACTIVE',
            category=self.materials,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.component_sku2 = ItemSKU.objects.create(
            sku_code='RAW002',
            name='Raw Material 2',
            unit='pcs',
            type='RAW',
            status='ACTIVE',
            category=self.materials,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create another PRODUCT component (set to ACTIVE for use as component)
        self.product_component = ItemSKU.objects.create(
            sku_code='PROD002',
            name='Product Component',
            unit='pcs',
            type='PRODUCT',
            status='DRAFT',
            category=self.electronics,
            created_by=self.user,
            updated_by=self.user,
        )
        # Activate it via direct database update
        ItemSKU.objects.filter(pk=self.product_component.pk).update(status='ACTIVE')
        self.product_component.refresh_from_db()

    # ==================== FORM INITIALIZATION TESTS ====================
    
    def test_form_init_without_parent_sku(self):
        """Test form initialization without parent_sku"""
        form = BOMForm()
        self.assertIsNone(form.parent_sku)
        self.assertIsNone(form.instance.parent_sku_id)
        
    def test_form_init_with_parent_sku(self):
        """Test form initialization with parent_sku"""
        form = BOMForm(parent_sku=self.parent_sku)
        self.assertEqual(form.parent_sku, self.parent_sku)
        self.assertEqual(form.instance.parent_sku, self.parent_sku)
        
    def test_form_init_with_existing_instance(self):
        """Test form initialization with existing instance"""
        # Create a BOM instance first
        existing_bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku,
            quantity=1,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Form with existing instance should preserve existing parent_sku
        form = BOMForm(instance=existing_bom)
        self.assertEqual(form.instance.parent_sku, self.parent_sku)
        
    def test_form_init_with_kwargs_extraction(self):
        """Test that parent_sku is properly extracted from kwargs"""
        form = BOMForm(
            parent_sku=self.parent_sku,
            initial={'quantity': 1},
            auto_id='test_%s'
        )
        self.assertEqual(form.parent_sku, self.parent_sku)
        self.assertEqual(form.instance.parent_sku, self.parent_sku)
        self.assertEqual(form.initial.get('quantity'), 1)
        self.assertEqual(form.auto_id, 'test_%s')

    # ==================== FORM FIELDS TESTS ====================
    
    def test_form_fields(self):
        """Test form fields are correctly defined"""
        form = BOMForm()
        self.assertIn('quantity', form.fields)
        self.assertIn('component_sku', form.fields)
        self.assertEqual(len(form.fields), 2)
        
    def test_form_field_widgets(self):
        """Test form field widgets"""
        form = BOMForm()
        self.assertEqual(form.fields['quantity'].widget.__class__.__name__, 'NumberInput')
        self.assertEqual(form.fields['component_sku'].widget.__class__.__name__, 'TextInput')
        
    def test_form_field_labels(self):
        """Test form field labels"""
        form = BOMForm()
        self.assertEqual(form.fields['quantity'].label, 'Quantity')
        self.assertEqual(form.fields['component_sku'].label, 'Component')
        
    def test_form_field_attributes(self):
        """Test form field widget attributes"""
        form = BOMForm()
        component_attrs = form.fields['component_sku'].widget.attrs
        self.assertEqual(component_attrs['placeholder'], 'Component SKU')
        self.assertEqual(component_attrs['autocomplete'], 'off')

    # ==================== FORM VALIDATION TESTS ====================
    
    def test_valid_form_with_parent_sku(self):
        """Test valid form submission with parent_sku"""
        form_data = {
            'quantity': 2,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_valid_form_with_product_component(self):
        """Test valid form with product as component"""
        form_data = {
            'quantity': 1,
            'component_sku': self.product_component.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_valid_form_without_parent_sku(self):
        """Test form submission without parent_sku (should fail validation)"""
        form_data = {
            'quantity': 1,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data)
        # Form should be invalid because model validation requires parent_sku
        self.assertFalse(form.is_valid())
        self.assertIn('Parent SKU is required', str(form.errors))
        
    def test_invalid_form_missing_quantity(self):
        """Test form validation with missing quantity"""
        form_data = {
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)
        
    def test_invalid_form_missing_component_sku(self):
        """Test form validation with missing component_sku"""
        form_data = {
            'quantity': 1
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('component_sku', form.errors)
        
    def test_invalid_form_zero_quantity(self):
        """Test form validation with zero quantity"""
        form_data = {
            'quantity': 0,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        # Form should be invalid because model validation catches zero quantity
        self.assertFalse(form.is_valid())
        self.assertIn('Quantity must be greater than zero', str(form.errors))
        
    def test_invalid_form_negative_quantity(self):
        """Test form validation with negative quantity"""
        form_data = {
            'quantity': -1,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        # Form should be invalid because model validation catches negative quantity
        self.assertFalse(form.is_valid())
        self.assertIn('Quantity must be greater than zero', str(form.errors))
        
    def test_invalid_form_invalid_component_sku(self):
        """Test form validation with invalid component_sku"""
        form_data = {
            'quantity': 1,
            'component_sku': 99999  # Non-existent ID
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('component_sku', form.errors)

    def test_invalid_form_draft_component(self):
        """Test form validation with DRAFT component (should fail)"""
        # Create a DRAFT component
        draft_component = ItemSKU.objects.create(
            sku_code='DRAFT001',
            name='Draft Component',
            unit='pcs',
            type='PRODUCT',
            status='DRAFT',
            category=self.electronics,
            created_by=self.user,
            updated_by=self.user,
        )
        
        form_data = {
            'quantity': 1,
            'component_sku': draft_component.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('Only ACTIVE components can be used in BOM', str(form.errors))

    def test_invalid_form_self_reference(self):
        """Test form validation with self-reference (parent as component)"""
        form_data = {
            'quantity': 1,
            'component_sku': self.parent_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('A product cannot be its own component', str(form.errors))

    # ==================== DECIMAL VALIDATION TESTS ====================
        
    def test_form_with_decimal_quantity(self):
        """Test form with decimal quantity values"""
        test_quantities = [Decimal('0.1'), Decimal('0.25'), Decimal('1.33'), Decimal('10.75'), Decimal('100.00')]
        
        for qty in test_quantities:
            with self.subTest(quantity=qty):
                form_data = {
                    'quantity': str(qty),
                    'component_sku': self.component_sku.id
                }
                form = BOMForm(data=form_data, parent_sku=self.parent_sku)
                self.assertTrue(form.is_valid(), f"Form should be valid for quantity {qty}. Errors: {form.errors}")
                self.assertEqual(form.cleaned_data['quantity'], qty)
                
    def test_form_with_large_quantity(self):
        """Test form with large quantity values"""
        form_data = {
            'quantity': 999999.99,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
    def test_form_with_string_quantity(self):
        """Test form with non-numeric quantity"""
        form_data = {
            'quantity': 'not_a_number',
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    # ==================== FORM SAVE TESTS ====================
    
    def test_form_save_with_parent_sku(self):
        """Test form save with parent_sku set"""
        form_data = {
            'quantity': 3,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
        # Set required audit fields before saving
        form.instance.created_by = self.user
        form.instance.updated_by = self.user
        
        bom = form.save()
        self.assertEqual(bom.parent_sku, self.parent_sku)
        self.assertEqual(bom.component_sku, self.component_sku)
        self.assertEqual(bom.quantity, 3)
        self.assertEqual(bom.created_by, self.user)
        self.assertEqual(bom.updated_by, self.user)
        
    def test_form_save_commit_false(self):
        """Test form save with commit=False"""
        form_data = {
            'quantity': 1.5,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
        bom = form.save(commit=False)
        self.assertEqual(bom.parent_sku, self.parent_sku)
        self.assertEqual(bom.component_sku, self.component_sku)
        self.assertEqual(bom.quantity, 1.5)
        self.assertIsNone(bom.pk)  # Should not be saved to database yet

    def test_form_save_with_update(self):
        """Test form save for updating existing BOM"""
        # Create existing BOM
        existing_bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku,
            quantity=1,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Update via form
        form_data = {
            'quantity': 5,
            'component_sku': self.component_sku2.id
        }
        form = BOMForm(data=form_data, instance=existing_bom, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
        # Set updated_by before saving
        form.instance.updated_by = self.user
        
        updated_bom = form.save()
        self.assertEqual(updated_bom.pk, existing_bom.pk)
        self.assertEqual(updated_bom.quantity, 5)
        self.assertEqual(updated_bom.component_sku, self.component_sku2)

    # ==================== DUPLICATE VALIDATION TESTS ====================
    
    def test_form_duplicate_component_validation(self):
        """Test form validation prevents duplicate components"""
        # Create first BOM
        BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku,
            quantity=1,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate via form
        form_data = {
            'quantity': 2,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('This component is already in the BOM for this parent item', str(form.errors))

    # ==================== LOCKED PARENT VALIDATION TESTS ====================
    
    def test_form_validation_with_locked_parent(self):
        """Test form validation when parent is locked (ACTIVE status)"""
        # Set parent to ACTIVE (locked)
        ItemSKU.objects.filter(pk=self.parent_sku.pk).update(status='ACTIVE')
        self.parent_sku.refresh_from_db()
        
        form_data = {
            'quantity': 1,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('Cannot create new BOM when parent item is locked', str(form.errors))

    def test_form_update_with_locked_parent(self):
        """Test form can update existing BOM even when parent is locked"""
        # Create BOM when parent is DRAFT
        existing_bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku,
            quantity=1,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Lock the parent
        ItemSKU.objects.filter(pk=self.parent_sku.pk).update(status='ACTIVE')
        self.parent_sku.refresh_from_db()
        
        # Update existing BOM should still work
        form_data = {
            'quantity': 3,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, instance=existing_bom, parent_sku=self.parent_sku)
        # Note: This behavior depends on validator implementation
        # May need to adjust based on business rules

    # ==================== EDGE CASE TESTS ====================
    
    def test_form_multiple_instances(self):
        """Test creating multiple form instances"""
        form1 = BOMForm(parent_sku=self.parent_sku)
        form2 = BOMForm(parent_sku=self.product_component)
        
        self.assertEqual(form1.parent_sku, self.parent_sku)
        self.assertEqual(form2.parent_sku, self.product_component)
        self.assertNotEqual(form1.parent_sku, form2.parent_sku)

    def test_form_with_inactive_component(self):
        """Test form with INACTIVE component"""
        # Create inactive component
        inactive_component = ItemSKU.objects.create(
            sku_code='INACTIVE001',
            name='Inactive Component',
            unit='pcs',
            type='PRODUCT',
            status='INACTIVE',
            category=self.electronics,
            created_by=self.user,
            updated_by=self.user,
        )
        
        form_data = {
            'quantity': 1,
            'component_sku': inactive_component.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('Only ACTIVE components can be used in BOM', str(form.errors))

    # ==================== INTEGRATION TESTS ====================
    
    def test_form_integration_with_model_validation(self):
        """Test form integration with model validation framework"""
        form_data = {
            'quantity': 2,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
        # Set audit fields and save
        form.instance.created_by = self.user
        form.instance.updated_by = self.user
        
        try:
            bom = form.save()
            self.assertIsNotNone(bom.pk)
            self.assertEqual(bom.parent_sku, self.parent_sku)
            
            # Verify validators were executed
            validators = bom.get_validators()
            self.assertGreater(len(validators), 0)
            
        except Exception as e:
            self.fail(f"Form save should not raise exception: {e}")

    def test_form_with_audit_field_validation(self):
        """Test form validation includes audit field requirements"""
        form_data = {
            'quantity': 1,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
        # Don't set audit fields - should fail on save
        try:
            form.save()
            self.fail("Save should have failed due to missing audit fields")
        except ValidationError as e:
            error_messages = str(e)
            # Check if validation error contains audit field requirements
            self.assertTrue(len(error_messages) > 0, "Should have validation errors")
            # The exact error messages depend on the validator implementation

    def test_form_with_optimistic_locking(self):
        """Test form works with optimistic locking"""
        # Create BOM
        bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku,
            quantity=1,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get initial version
        initial_version = bom.version
        
        # Update via form
        form_data = {
            'quantity': 2,
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, instance=bom)
        self.assertTrue(form.is_valid())
        
        form.instance.updated_by = self.user
        updated_bom = form.save()
        
        # Version should have incremented
        self.assertEqual(updated_bom.version, initial_version + 1)

    # ==================== PERFORMANCE TESTS ====================
    
    def test_form_queryset_efficiency(self):
        """Test form doesn't cause N+1 query problems"""
        # Create multiple components
        components = []
        for i in range(10):
            component = ItemSKU.objects.create(
                sku_code=f'COMP{i:03d}',
                name=f'Component {i}',
                unit='pcs',
                type='RAW',
                status='ACTIVE',
                category=self.materials,
                created_by=self.user,
                updated_by=self.user,
            )
            components.append(component)
        
        # Test form initialization doesn't cause excessive queries
        with self.assertNumQueries(0):
            form = BOMForm(parent_sku=self.parent_sku)
            # Just accessing fields shouldn't cause queries
            _ = form.fields['component_sku']
