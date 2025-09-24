"""
Test StockMovementImage Forms

Tests for StockMovementImage form functionality.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from inventory.models import StockMovementImage, StockMovement, Warehouse
from inventory.forms import (
    StockMovementImageForm,
    StockMovementImageBulkUploadForm,
    StockMovementImageUpdateForm
)
from catalog.models import ItemSKU


class StockMovementImageFormTests(TestCase):
    """Test cases for StockMovementImage forms"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            code='TW01',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create stock movement
        self.stock_movement = StockMovement.objects.create(
            reference_type=StockMovement.ReferenceType.ADJUST,
            warehouse=self.warehouse,
            note='Test movement',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test image file (minimal valid JPEG)
        # This is a minimal 1x1 pixel JPEG file
        jpeg_data = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01'
            b'\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff'
            b'\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        )
        
        self.image_file = SimpleUploadedFile(
            "test.jpg",
            jpeg_data,
            content_type="image/jpeg"
        )
    
    def test_stock_movement_image_form_valid(self):
        """Test valid form submission"""
        form_data = {
            'stock_movement': self.stock_movement.id,
            'caption': 'Test Receipt',
            'is_primary': True,
            'note': 'This is a test receipt document'
        }
        
        form = StockMovementImageForm(data=form_data, files={'image': self.image_file})
        self.assertTrue(form.is_valid())
        
        # Test saving with user
        form.set_user(self.user)
        image = form.save()
        
        self.assertEqual(image.stock_movement, self.stock_movement)
        self.assertEqual(image.caption, 'Test Receipt')
        self.assertTrue(image.is_primary)
        self.assertEqual(image.note, 'This is a test receipt document')
        self.assertEqual(image.created_by, self.user)
        self.assertEqual(image.updated_by, self.user)
    
    def test_stock_movement_image_form_with_stock_movement_kwarg(self):
        """Test form initialization with stock_movement kwarg"""
        form = StockMovementImageForm(stock_movement=self.stock_movement)
        
        # Should have limited queryset to only this stock movement
        self.assertEqual(form.fields['stock_movement'].queryset.count(), 1)
        self.assertEqual(form.fields['stock_movement'].initial, self.stock_movement)
    
    def test_stock_movement_image_update_form(self):
        """Test update form for existing images"""
        # Create an image first
        image = StockMovementImage.objects.create(
            stock_movement=self.stock_movement,
            image=self.image_file,
            caption='Original Caption',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test update form
        form_data = {
            'caption': 'Updated Caption',
            'is_primary': True,
            'note': 'Updated note'
        }
        
        form = StockMovementImageUpdateForm(data=form_data, instance=image)
        self.assertTrue(form.is_valid())
        
        # Test saving with user
        form.set_user(self.user)
        updated_image = form.save()
        
        self.assertEqual(updated_image.caption, 'Updated Caption')
        self.assertTrue(updated_image.is_primary)
        self.assertEqual(updated_image.note, 'Updated note')
        self.assertEqual(updated_image.updated_by, self.user)
    
    def test_bulk_upload_form_validation(self):
        """Test bulk upload form validation"""
        form_data = {
            'stock_movement': self.stock_movement.id,
            'set_first_as_primary': True
        }
        
        # Create multiple test files
        image_files = [
            SimpleUploadedFile(f"test{i}.jpg", b"fake image content", content_type="image/jpeg")
            for i in range(3)
        ]
        
        form = StockMovementImageBulkUploadForm(data=form_data)
        form.files = type('MockFiles', (), {'getlist': lambda self, key: image_files})()
        
        # Test validation
        cleaned_images = form.clean_images()
        self.assertEqual(len(cleaned_images), 3)
    
    def test_form_field_widgets(self):
        """Test that form fields have correct widgets and attributes"""
        form = StockMovementImageForm()
        
        # Test image field widget
        self.assertEqual(form.fields['image'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['image'].widget.attrs['accept'], 'image/*,application/pdf')
        
        # Test caption field widget
        self.assertEqual(form.fields['caption'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['caption'].widget.attrs['maxlength'], '255')
        
        # Test note field widget
        self.assertEqual(form.fields['note'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['note'].widget.attrs['rows'], 3)
        
        # Test is_primary field widget
        self.assertEqual(form.fields['is_primary'].widget.attrs['class'], 'form-check-input')
    
    def test_form_help_texts(self):
        """Test that form fields have correct help texts"""
        form = StockMovementImageForm()
        
        self.assertIn('Max size: 10MB', form.fields['image'].help_text)
        self.assertIn('max 255 characters', form.fields['caption'].help_text)
        self.assertIn('primary document', form.fields['is_primary'].help_text)
        self.assertIn('Additional notes', form.fields['note'].help_text)