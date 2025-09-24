"""
Test StockMovementImage Model

Basic tests for the StockMovementImage model functionality.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from inventory.models import StockMovementImage, StockMovement, Warehouse
from catalog.models import ItemSKU


class StockMovementImageModelTests(TestCase):
    """Test cases for StockMovementImage model"""
    
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
        
        # Create item
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.RAW,
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
    
    def test_model_import(self):
        """Test that StockMovementImage can be imported"""
        from inventory.models import StockMovementImage
        self.assertTrue(hasattr(StockMovementImage, '_meta'))
    
    def test_model_creation(self):
        """Test basic model creation"""
        # Create a simple uploaded file for testing
        image_file = SimpleUploadedFile(
            "test.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        image = StockMovementImage.objects.create(
            stock_movement=self.stock_movement,
            image=image_file,
            caption='Test image',
            note='Test note',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(image.stock_movement, self.stock_movement)
        self.assertEqual(image.caption, 'Test image')
        self.assertEqual(image.note, 'Test note')
        self.assertFalse(image.is_primary)  # Default should be False
    
    def test_model_string_representation(self):
        """Test __str__ method"""
        image_file = SimpleUploadedFile(
            "test.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        image = StockMovementImage.objects.create(
            stock_movement=self.stock_movement,
            image=image_file,
            caption='Receipt Document',
            created_by=self.user,
            updated_by=self.user
        )
        
        expected_str = f"Movement {self.stock_movement.id} Image - Receipt Document"
        self.assertEqual(str(image), expected_str)
    
    def test_primary_image_logic(self):
        """Test primary image constraint logic"""
        image_file1 = SimpleUploadedFile(
            "test1.jpg",
            b"fake image content 1",
            content_type="image/jpeg"
        )
        
        image_file2 = SimpleUploadedFile(
            "test2.jpg", 
            b"fake image content 2",
            content_type="image/jpeg"
        )
        
        # Create first image as primary
        image1 = StockMovementImage.objects.create(
            stock_movement=self.stock_movement,
            image=image_file1,
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create second image as primary - should make first one non-primary
        image2 = StockMovementImage.objects.create(
            stock_movement=self.stock_movement,
            image=image_file2,
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Refresh from database
        image1.refresh_from_db()
        image2.refresh_from_db()
        
        # Only image2 should be primary now
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)
    
    def test_validators(self):
        """Test that validators are properly configured"""
        image = StockMovementImage()
        validators = image.get_validators()
        
        # Should have 3 validators
        self.assertEqual(len(validators), 3)
        
        validator_classes = [v.__class__.__name__ for v in validators]
        expected_validators = [
            'StockMovementImageValidator',
            'StockMovementImagePrimaryValidator', 
            'StockMovementImageBusinessRulesValidator'
        ]
        
        for expected in expected_validators:
            self.assertIn(expected, validator_classes)