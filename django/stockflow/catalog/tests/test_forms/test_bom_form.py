from django.test import TestCase
from django.contrib.auth.models import User
from catalog.forms.bom_form import BOMForm
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from decimal import Decimal


class BOMFormTest(TestCase):
    def setUp(self):
        """Set up test data for BOM form tests"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for BOM form tests',
            is_active=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create parent item (PRODUCT in DRAFT status)
        self.parent_sku = ItemSKU.objects.create(
            sku_code='PROD001',
            name='Product 1',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create component item (RAW material)
        self.component_sku = ItemSKU.objects.create(
            sku_code='RAW001',
            name='Raw Material 1',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
        # Create another component for testing
        self.component_sku2 = ItemSKU.objects.create(
            sku_code='RAW002',
            name='Raw Material 2',
            unit='pcs',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )

    # ==================== FORM INITIALIZATION TESTS ====================
    
    def test_form_init_without_parent_sku(self):
        """Test form initialization without parent_sku"""
        form = BOMForm()
        self.assertIsNone(form.parent_sku)
        # Don't check form.instance.parent_sku as it will raise RelatedObjectDoesNotExist
        self.assertIsNone(form.instance.parent_sku_id)
        
    def test_form_init_with_parent_sku(self):
        """Test form initialization with parent_sku"""
        form = BOMForm(parent_sku=self.parent_sku)
        self.assertEqual(form.parent_sku, self.parent_sku)
        self.assertEqual(form.instance.parent_sku, self.parent_sku)
        
    def test_form_init_with_existing_instance(self):
        """Test form initialization with existing instance (should not override parent_sku)"""
        # Create a BOM instance first
        from catalog.models.bom import BOM
        existing_bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku,
            quantity=Decimal('1.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Form with existing instance should not override parent_sku
        form = BOMForm(instance=existing_bom, parent_sku=self.component_sku2)
        self.assertEqual(form.parent_sku, self.component_sku2)
        # Instance parent_sku should remain unchanged for existing instances
        self.assertEqual(form.instance.parent_sku, self.parent_sku)

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
            'quantity': '2.5',
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_valid_form_without_parent_sku(self):
        """Test valid form submission without parent_sku (should fail model validation)"""
        form_data = {
            'quantity': '1.0',
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
            'quantity': '1.0'
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('component_sku', form.errors)
        
    def test_invalid_form_zero_quantity(self):
        """Test form validation with zero quantity"""
        form_data = {
            'quantity': '0',
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        # Form should be invalid because model validation catches zero quantity
        self.assertFalse(form.is_valid())
        self.assertIn('Quantity must be greater than zero', str(form.errors))
        
    def test_invalid_form_negative_quantity(self):
        """Test form validation with negative quantity"""
        form_data = {
            'quantity': '-1.0',
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        # Form should be invalid because model validation catches negative quantity
        self.assertFalse(form.is_valid())
        self.assertIn('Quantity must be greater than zero', str(form.errors))
        
    def test_invalid_form_invalid_component_sku(self):
        """Test form validation with invalid component_sku"""
        form_data = {
            'quantity': '1.0',
            'component_sku': 99999  # Non-existent ID
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('component_sku', form.errors)
        
    def test_form_with_invalid_decimal_places(self):
        """Test form with more than 2 decimal places (should be invalid)"""
        form_data = {
            'quantity': '1.333',  # 3 decimal places
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertFalse(form.is_valid())
        self.assertIn('Ensure that there are no more than 2 decimal places', str(form.errors))

    # ==================== FORM SAVE TESTS ====================
    
    def test_form_save_with_parent_sku(self):
        """Test form save with parent_sku set"""
        form_data = {
            'quantity': '3.0',
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
        self.assertEqual(bom.quantity, Decimal('3.0'))
        self.assertEqual(bom.created_by, self.user)
        self.assertEqual(bom.updated_by, self.user)
        
    def test_form_save_commit_false(self):
        """Test form save with commit=False"""
        form_data = {
            'quantity': '1.5',
            'component_sku': self.component_sku.id
        }
        form = BOMForm(data=form_data, parent_sku=self.parent_sku)
        self.assertTrue(form.is_valid())
        
        bom = form.save(commit=False)
        self.assertEqual(bom.parent_sku, self.parent_sku)
        self.assertEqual(bom.component_sku, self.component_sku)
        self.assertEqual(bom.quantity, Decimal('1.5'))
        self.assertIsNone(bom.pk)  # Should not be saved to database yet

    # ==================== EDGE CASE TESTS ====================
    
    def test_form_with_decimal_quantity(self):
        """Test form with decimal quantity values (max 2 decimal places)"""
        test_quantities = ['0.1', '0.25', '1.33', '10.75', '100.00']
        
        for qty in test_quantities:
            with self.subTest(quantity=qty):
                form_data = {
                    'quantity': qty,
                    'component_sku': self.component_sku.id
                }
                form = BOMForm(data=form_data, parent_sku=self.parent_sku)
                self.assertTrue(form.is_valid(), f"Form should be valid for quantity {qty}. Errors: {form.errors}")
                self.assertEqual(str(form.cleaned_data['quantity']), qty)
                
    def test_form_with_large_quantity(self):
        """Test form with large quantity values"""
        form_data = {
            'quantity': '999999.99',
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
        
    def test_form_multiple_instances(self):
        """Test creating multiple form instances"""
        form1 = BOMForm(parent_sku=self.parent_sku)
        form2 = BOMForm(parent_sku=self.component_sku2)
        
        self.assertEqual(form1.parent_sku, self.parent_sku)
        self.assertEqual(form2.parent_sku, self.component_sku2)
        self.assertNotEqual(form1.parent_sku, form2.parent_sku)

    # ==================== INTEGRATION TESTS ====================
    
    def test_form_integration_with_model_validation(self):
        """Test form integration with model validation"""
        # This test verifies that form validation works with model validation
        form_data = {
            'quantity': '2.0',
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
        except Exception as e:
            self.fail(f"Form save should not raise exception: {e}")
            
    def test_form_with_kwargs_extraction(self):
        """Test that parent_sku is properly extracted from kwargs"""
        # Test with additional kwargs
        form = BOMForm(
            parent_sku=self.parent_sku,
            initial={'quantity': '1.0'},
            auto_id='test_%s'
        )
        self.assertEqual(form.parent_sku, self.parent_sku)
        self.assertEqual(form.instance.parent_sku, self.parent_sku)
        self.assertEqual(form.initial.get('quantity'), '1.0')
        self.assertEqual(form.auto_id, 'test_%s')