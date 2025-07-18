from django.test import TestCase
from django.contrib.auth.models import User
from django import forms
from catalog.forms.bom_update_form import BOMUpdateForm
from catalog.models.item import ItemSKU
from catalog.models.category import Category
from catalog.models.bom import BOM
from decimal import Decimal


class BOMUpdateFormTest(TestCase):
    """
    Test BOMUpdateForm - Focus on form behavior, field restrictions, and validation.
    """
    
    def setUp(self):
        """Set up test data for BOM update form tests"""
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
        
        # Create component items
        self.component_sku1 = ItemSKU.objects.create(
            sku_code='RAW001',
            name='Raw Material 1',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,
            category=self.category,
            created_by=self.user,
            updated_by=self.user,
        )
        
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
        
        # Create existing BOM
        self.bom = BOM.objects.create(
            parent_sku=self.parent_sku,
            component_sku=self.component_sku1,
            quantity=Decimal('2.0'),
            created_by=self.user,
            updated_by=self.user
        )

    # ==================== FORM INITIALIZATION TESTS ====================
    
    def test_form_init_with_existing_instance_disables_fields(self):
        """Test form initialization with existing instance disables parent and component fields"""
        form = BOMUpdateForm(instance=self.bom)
        
        # Check that parent_sku and component_sku are disabled
        self.assertTrue(form.fields['parent_sku'].disabled)
        self.assertTrue(form.fields['component_sku'].disabled)
        
        # Check that quantity is not disabled
        self.assertFalse(form.fields['quantity'].disabled)
        
    def test_form_init_without_instance_does_not_disable_fields(self):
        """Test form initialization without instance does not disable fields"""
        form = BOMUpdateForm()
        
        # Fields should not be disabled for new instances
        self.assertFalse(form.fields['parent_sku'].disabled)
        self.assertFalse(form.fields['component_sku'].disabled)
        self.assertFalse(form.fields['quantity'].disabled)
        
    def test_form_init_sets_help_text_and_labels(self):
        """Test form initialization sets appropriate help text and labels"""
        form = BOMUpdateForm(instance=self.bom)
        
        self.assertIn('You can only change the quantity', form.fields['quantity'].help_text)
        self.assertEqual(form.fields['parent_sku'].label, 'Parent Item (Read-only)')
        self.assertEqual(form.fields['component_sku'].label, 'Component Item (Read-only)')

    # ==================== FORM FIELDS TESTS ====================
    
    def test_form_fields(self):
        """Test form fields are correctly defined"""
        form = BOMUpdateForm()
        self.assertIn('parent_sku', form.fields)
        self.assertIn('component_sku', form.fields)
        self.assertIn('quantity', form.fields)
        self.assertEqual(len(form.fields), 3)
        
    def test_form_field_widgets(self):
        """Test form field widgets"""
        form = BOMUpdateForm()
        
        # Check quantity widget attributes
        quantity_widget = form.fields['quantity'].widget
        self.assertEqual(quantity_widget.attrs['step'], '0.01')
        self.assertEqual(quantity_widget.attrs['min'], '0.01')

    # ==================== QUANTITY VALIDATION TESTS ====================
    
    def test_clean_quantity_valid_values(self):
        """Test clean_quantity with valid values"""
        form = BOMUpdateForm(instance=self.bom)
        
        valid_quantities = [0.01, 1.0, 2.5, 10.75, 999.99]
        for qty in valid_quantities:
            with self.subTest(quantity=qty):
                form.cleaned_data = {'quantity': Decimal(str(qty))}
                result = form.clean_quantity()
                self.assertEqual(result, Decimal(str(qty)))
    
    def test_clean_quantity_zero_raises_error(self):
        """Test clean_quantity with zero raises error"""
        form = BOMUpdateForm(instance=self.bom)
        form.cleaned_data = {'quantity': Decimal('0')}
        
        with self.assertRaises(forms.ValidationError) as cm:
            form.clean_quantity()
        self.assertIn('greater than zero', str(cm.exception))
    
    def test_clean_quantity_negative_raises_error(self):
        """Test clean_quantity with negative value raises error"""
        form = BOMUpdateForm(instance=self.bom)
        form.cleaned_data = {'quantity': Decimal('-1.0')}
        
        with self.assertRaises(forms.ValidationError) as cm:
            form.clean_quantity()
        self.assertIn('greater than zero', str(cm.exception))
    
    def test_clean_quantity_too_many_decimals_raises_error(self):
        """Test clean_quantity with more than 2 decimal places raises error"""
        form = BOMUpdateForm(instance=self.bom)
        form.cleaned_data = {'quantity': Decimal('1.333')}
        
        with self.assertRaises(forms.ValidationError) as cm:
            form.clean_quantity()
        self.assertIn('more than 2 decimal places', str(cm.exception))

    # ==================== FORM CLEAN TESTS ====================
    
    def test_clean_prevents_parent_sku_change(self):
        """Test clean method preserves original parent_sku for existing instances"""
        form_data = {
            'parent_sku': self.component_sku2.id,  # Different parent in form data
            'component_sku': self.component_sku1.id,
            'quantity': '2.0'
        }
        form = BOMUpdateForm(data=form_data, instance=self.bom)
        
        # Form should be valid because disabled fields are preserved
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # But cleaned_data should have original parent_sku
        self.assertEqual(form.cleaned_data['parent_sku'], self.parent_sku)
    
    def test_clean_prevents_component_sku_change(self):
        """Test clean method preserves original component_sku for existing instances"""
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku2.id,  # Different component in form data
            'quantity': '2.0'
        }
        form = BOMUpdateForm(data=form_data, instance=self.bom)
        
        # Form should be valid because disabled fields are preserved
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # But cleaned_data should have original component_sku
        self.assertEqual(form.cleaned_data['component_sku'], self.component_sku1)
    
    def test_clean_allows_quantity_change(self):
        """Test clean method allows changing quantity for existing instance"""
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': '3.5'  # Changed quantity
        }
        form = BOMUpdateForm(data=form_data, instance=self.bom)
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        self.assertEqual(form.cleaned_data['quantity'], Decimal('3.5'))

    # ==================== FORM SAVE TESTS ====================
    
    def test_form_save_updates_only_quantity(self):
        """Test form save updates only quantity"""
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
            'quantity': '5.0'
        }
        form = BOMUpdateForm(data=form_data, instance=self.bom)
        self.assertTrue(form.is_valid())
        
        updated_bom = form.save()
        
        # Check that quantity was updated
        self.assertEqual(updated_bom.quantity, Decimal('5.0'))
        
        # Check that parent and component remain unchanged
        self.assertEqual(updated_bom.parent_sku, self.parent_sku)
        self.assertEqual(updated_bom.component_sku, self.component_sku1)

    # ==================== EDGE CASE TESTS ====================
    
    def test_form_with_new_instance_allows_all_changes(self):
        """Test form with new instance (no pk) allows all field changes"""
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku2.id,
            'quantity': '1.0'
        }
        # Create form without instance (new BOM)
        form = BOMUpdateForm(data=form_data)
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_form_handles_missing_quantity(self):
        """Test form handles missing quantity field"""
        form_data = {
            'parent_sku': self.parent_sku.id,
            'component_sku': self.component_sku1.id,
        }
        form = BOMUpdateForm(data=form_data, instance=self.bom)
        
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)
