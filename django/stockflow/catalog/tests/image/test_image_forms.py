"""
ItemImage Form Tests

This module contains comprehensive tests for ItemImage forms.
Tests cover form validation, business rules, and functionality.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User

from catalog.tests.image.test_image_file_mixin import TestImageFileMixin
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category
from catalog.forms.image_form import (
    ItemImageForm, 
    ItemImageBulkUploadForm, 
    ItemImageUpdateForm
)


class ItemImageFormTest(TestImageFileMixin,TestCase):
    """Test case for ItemImageForm"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for items',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test items
        self.active_item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Active Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start with DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Now activate the item for image upload
        self.active_item.status = ItemSKU.Status.ACTIVE
        self.active_item.save()
        
        self.draft_item = ItemSKU.objects.create(
            sku_code='TEST-002',
            name='Draft Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_form_fields_present(self):
        """Test that all required fields are present"""
        form = ItemImageForm()
        expected_fields = ['item', 'image', 'caption', 'is_primary']
        
        for field in expected_fields:
            self.assertIn(field, form.fields)
    
    def test_valid_form_data(self):
        """Test form with valid data"""
        image_file = self._create_test_image()
        form_data = {
            'item': self.active_item.pk,
            'caption': 'Test image caption',
            'is_primary': True
        }
        form_files = {
            'image': image_file
        }
        
        form = ItemImageForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_without_image(self):
        """Test form validation without image file"""
        form_data = {
            'item': self.active_item.pk,
            'caption': 'Test caption',
            'is_primary': False
        }
        
        form = ItemImageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
    
    def test_form_without_item(self):
        """Test form validation without item"""
        image_file = self._create_test_image()
        form_data = {
            'caption': 'Test caption',
            'is_primary': False
        }
        form_files = {
            'image': image_file
        }
        
        form = ItemImageForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('item', form.errors)
    
    def test_form_with_long_caption(self):
        """Test form validation with caption exceeding max length"""
        image_file = self._create_test_image()
        long_caption = 'x' * 256  # Exceeds 255 character limit
        
        form_data = {
            'item': self.active_item.pk,
            'caption': long_caption,
            'is_primary': False
        }
        form_files = {
            'image': image_file
        }
        
        form = ItemImageForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('caption', form.errors)
    
    def test_form_queryset_filters_active_items(self):
        """Test that form only shows active items in queryset"""
        form = ItemImageForm()
        item_queryset = form.fields['item'].queryset
        
        # Should contain active item
        self.assertIn(self.active_item, item_queryset)
        # Should not contain draft item (not active)
        self.assertNotIn(self.draft_item, item_queryset)
    
    def test_form_save_with_user(self):
        """Test form save with user context"""
        image_file = self._create_test_image()
        form_data = {
            'item': self.active_item.pk,
            'caption': 'Test image',
            'is_primary': True
        }
        form_files = {
            'image': image_file
        }
        
        form = ItemImageForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
        
        form.set_user(self.user)
        instance = form.save()
        
        self.assertEqual(instance.created_by, self.user)
        self.assertEqual(instance.updated_by, self.user)
        self.assertEqual(instance.item, self.active_item)
        self.assertEqual(instance.caption, 'Test image')
        self.assertTrue(instance.is_primary)
    
    def test_form_edit_mode_disables_item_field(self):
        """Test that item field is disabled in edit mode"""
        # Create an existing image
        existing_image = ItemImage.objects.create(
            item=self.active_item,
            image=self._create_test_image(),
            caption='Existing image',
            created_by=self.user,
            updated_by=self.user
        )
        
        form = ItemImageForm(instance=existing_image)
        self.assertTrue(form.fields['item'].widget.attrs.get('disabled'))


class ItemImageBulkUploadFormTest(TestImageFileMixin, TestCase):
    """Test case for ItemImageBulkUploadForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start with DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Now activate the item for image upload
        self.item.status = ItemSKU.Status.ACTIVE
        self.item.save()
    
    def test_form_fields_present(self):
        """Test that all required fields are present"""
        form = ItemImageBulkUploadForm()
        expected_fields = ['item', 'set_first_as_primary']
        
        for field in expected_fields:
            self.assertIn(field, form.fields)
        
        # Images field is handled by the view, not the form
        self.assertNotIn('images', form.fields)
    
    def test_valid_bulk_upload_form_data(self):
        """Test valid form data (images handled separately by view)"""
        form_data = {
            'item': self.item.pk,
            'set_first_as_primary': True
        }
        
        form = ItemImageBulkUploadForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Test cleaned data
        self.assertEqual(form.cleaned_data['item'], self.item)
        self.assertTrue(form.cleaned_data['set_first_as_primary'])
    
    def test_bulk_upload_missing_item(self):
        """Test validation when item is missing"""
        form_data = {
            'set_first_as_primary': True
        }
        
        form = ItemImageBulkUploadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('item', form.errors)
    
    def test_bulk_upload_item_queryset_filtering(self):
        """Test that only active items are available in queryset"""
        # Create inactive item - start with DRAFT then make inactive
        inactive_item = ItemSKU.objects.create(
            sku_code='INACTIVE-001',
            name='Inactive Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Make it inactive
        inactive_item.status = ItemSKU.Status.INACTIVE
        inactive_item.save()
        
        form = ItemImageBulkUploadForm()
        available_items = list(form.fields['item'].queryset)
        
        # Active item should be in queryset
        self.assertIn(self.item, available_items)
        # Inactive item should not be in queryset
        self.assertNotIn(inactive_item, available_items)
    
    def test_bulk_upload_default_values(self):
        """Test form default values"""
        form = ItemImageBulkUploadForm()
        
        # set_first_as_primary should default to True
        self.assertTrue(form.fields['set_first_as_primary'].initial)
    
    def test_bulk_upload_form_widget_classes(self):
        """Test form widget CSS classes"""
        form = ItemImageBulkUploadForm()
        
        # Test item field widget
        item_widget = form.fields['item'].widget
        self.assertIn('form-select', item_widget.attrs.get('class', ''))
        
        # Test checkbox widget
        checkbox_widget = form.fields['set_first_as_primary'].widget
        self.assertIn('form-check-input', checkbox_widget.attrs.get('class', ''))


class ItemImageUpdateFormTest(TestImageFileMixin, TestCase):
    """Test case for ItemImageUpdateForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start with DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Now activate the item for image upload
        self.item.status = ItemSKU.Status.ACTIVE
        self.item.save()
        
        # Create test image file
        image_file = self._create_test_image()
        self.image = ItemImage.objects.create(
            item=self.item,
            image=image_file,
            caption='Original caption',
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_form_fields_present(self):
        """Test that required fields are present"""
        form = ItemImageUpdateForm()
        expected_fields = ['caption', 'is_primary']
        
        for field in expected_fields:
            self.assertIn(field, form.fields)
        
        # Should not include image or item fields
        self.assertNotIn('image', form.fields)
        self.assertNotIn('item', form.fields)
    
    def test_update_form_valid_data(self):
        """Test update form with valid data"""
        form_data = {
            'caption': 'Updated caption',
            'is_primary': True
        }
        
        form = ItemImageUpdateForm(data=form_data, instance=self.image)
        self.assertTrue(form.is_valid())
    
    def test_update_form_save(self):
        """Test saving updated data"""
        form_data = {
            'caption': 'Updated caption',
            'is_primary': True
        }
        
        form = ItemImageUpdateForm(data=form_data, instance=self.image)
        self.assertTrue(form.is_valid())
        
        form.set_user(self.user)
        updated_image = form.save()
        
        # Refresh from database
        updated_image.refresh_from_db()
        
        self.assertEqual(updated_image.caption, 'Updated caption')
        self.assertTrue(updated_image.is_primary)
        self.assertEqual(updated_image.updated_by, self.user)
    
    def test_update_form_empty_caption(self):
        """Test update form with empty caption"""
        form_data = {
            'caption': '',
            'is_primary': False
        }
        
        form = ItemImageUpdateForm(data=form_data, instance=self.image)
        self.assertTrue(form.is_valid())  # Empty caption should be valid
        
        updated_image = form.save()
        self.assertEqual(updated_image.caption, '')


class ItemImageFormIntegrationTest(TestImageFileMixin, TestCase):
    """Integration tests for ItemImage forms"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Start with DRAFT
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        # Now activate the item for image upload
        self.item.status = ItemSKU.Status.ACTIVE
        self.item.save()
        
    def test_primary_image_workflow(self):
        """Test complete primary image workflow"""
        # 1. Upload first image as primary
        image1_file = self._create_test_image('image1.jpg')
        form1_data = {
            'item': self.item.pk,
            'caption': 'First image',
            'is_primary': True
        }
        form1_files = {'image': image1_file}
        
        form1 = ItemImageForm(data=form1_data, files=form1_files)
        self.assertTrue(form1.is_valid())
        
        form1.set_user(self.user)
        image1 = form1.save()
        
        self.assertTrue(image1.is_primary)
        
        # 2. Upload second image (non-primary)
        image2_file = self._create_test_image('image2.jpg')
        form2_data = {
            'item': self.item.pk,
            'caption': 'Second image',
            'is_primary': False
        }
        form2_files = {'image': image2_file}
        
        form2 = ItemImageForm(data=form2_data, files=form2_files)
        self.assertTrue(form2.is_valid())
        
        form2.set_user(self.user)
        image2 = form2.save()
        
        self.assertFalse(image2.is_primary)
        
        # 3. Update second image to be primary using update form
        update_form_data = {
            'caption': 'Updated second image',
            'is_primary': True
        }
        
        update_form = ItemImageUpdateForm(data=update_form_data, instance=image2)
        self.assertTrue(update_form.is_valid())
        
        update_form.set_user(self.user)
        updated_image2 = update_form.save()
        
        # Refresh both images from database
        image1.refresh_from_db()
        updated_image2.refresh_from_db()
        
        # Only image2 should be primary now
        self.assertFalse(image1.is_primary)
        self.assertTrue(updated_image2.is_primary)
        
        # Verify only one primary image exists
        primary_count = ItemImage.objects.filter(
            item=self.item, 
            is_primary=True
        ).count()
        self.assertEqual(primary_count, 1)
