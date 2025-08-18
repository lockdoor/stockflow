"""
ItemImage Model Tests

This module contains comprehensive tests for the ItemImage model.
Tests cover model creation, validation, business rules, and mixins functionality.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User

from catalog.tests.image.test_image_file_mixin import TestImageFileMixin
from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.models.category import Category


class ItemImageValidationTest(TestImageFileMixin, TestCase):
    """Test case for ItemImage validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for items',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create test image file
        self.test_image = self._create_test_image()
    
    def test_create_item_image(self):
        """Test creating a new ItemImage"""
        item_image = ItemImage.objects.create(
            item=self.item,
            image=self.test_image,
            caption='Test image caption',
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(item_image.item, self.item)
        self.assertEqual(item_image.caption, 'Test image caption')
        self.assertTrue(item_image.is_primary)
        self.assertEqual(item_image.created_by, self.user)
        self.assertIsNotNone(item_image.image)
    
    def test_string_representation(self):
        """Test __str__ method"""
        item_image = ItemImage.objects.create(
            item=self.item,
            image=self.test_image,
            caption='Test Caption',
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        expected = f"{self.item.sku_code} Image - Test Caption (Primary)"
        self.assertEqual(str(item_image), expected)
    
    def test_string_representation_without_caption(self):
        """Test __str__ method without caption"""
        item_image = ItemImage.objects.create(
            item=self.item,
            image=self.test_image,
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        expected = f"{self.item.sku_code} Image"
        self.assertEqual(str(item_image), expected)
    
    def test_image_properties(self):
        """Test image-related properties"""
        item_image = ItemImage.objects.create(
            item=self.item,
            image=self.test_image,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test image_url property
        self.assertIsNotNone(item_image.image_url)
        self.assertTrue(item_image.image_url.endswith('.jpg'))
        
        # Test image_name property
        self.assertIsNotNone(item_image.image_name)
        self.assertTrue(item_image.image_name.endswith('.jpg'))
        
        # Test file_size property
        self.assertGreater(item_image.file_size, 0)
        
        # Test file_extension property
        self.assertEqual(item_image.file_extension, '.jpg')
    
    def test_validators_loaded(self):
        """Test that validators are properly loaded"""
        item_image = ItemImage(
            item=self.item,
            image=self.test_image,
            created_by=self.user,
            updated_by=self.user
        )
        
        validators = item_image.get_validators()
        self.assertEqual(len(validators), 3)
        self.assertTrue(all(hasattr(v, 'validate') for v in validators))


class ItemImagePrimaryTest(TestImageFileMixin, TestCase):
    """Test case for ItemImage primary image functionality"""
    
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
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
    def test_primary_image_constraint(self):
        """Test that only one primary image is allowed per item"""
        # Create first primary image
        image1 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image1.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create second primary image - should automatically unset the first
        image2 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image2.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Refresh from database
        image1.refresh_from_db()
        image2.refresh_from_db()
        
        # Only the second image should be primary
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)
    
    def test_get_primary_image_for_item(self):
        """Test getting primary image for an item"""
        # No images initially
        primary = ItemImage.get_primary_for_item(self.item)
        self.assertIsNone(primary)
        
        # Create non-primary image
        image1 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image1.jpg'),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should return first image even if not primary
        primary = ItemImage.get_primary_for_item(self.item)
        self.assertEqual(primary, image1)
        
        # Create primary image
        image2 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image2.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should return primary image
        primary = ItemImage.get_primary_for_item(self.item)
        self.assertEqual(primary, image2)
    
    def test_set_primary_image(self):
        """Test setting an image as primary"""
        # Create two images
        image1 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image1.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        image2 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image2.jpg'),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Set image2 as primary
        ItemImage.set_primary_image(self.item, image2.id)
        
        # Refresh from database
        image1.refresh_from_db()
        image2.refresh_from_db()
        
        # Check primary status
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)
    
    def test_delete_primary_image(self):
        """Test deleting primary image sets another as primary"""
        # Create two images
        image1 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image1.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        image2 = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image('image2.jpg'),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Delete primary image
        image1.delete()
        
        # Refresh image2
        image2.refresh_from_db()
        
        # image2 should now be primary
        self.assertTrue(image2.is_primary)


class ItemImageBusinessRulesTest(TestImageFileMixin, TestCase):
    """Test case for ItemImage business rules"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            note='Test category for items',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.test_image = self._create_test_image()


class ItemImageMixinsTest(TestImageFileMixin, TestCase):
    """Test case for mixin functionality"""
    
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
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
      
    def test_auditable_mixin_fields(self):
        """Test that AuditableMixin fields are present"""
        item_image = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image(),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check audit fields
        self.assertEqual(item_image.created_by, self.user)
        self.assertEqual(item_image.updated_by, self.user)
        self.assertIsNotNone(item_image.created_at)
        self.assertIsNotNone(item_image.updated_at)
        self.assertIsNotNone(item_image.version)
    
    def test_validatable_mixin_functionality(self):
        """Test that ValidatableMixin functionality works"""
        item_image = ItemImage(
            item=self.item,
            image=self._create_test_image(),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should have get_validators method from ValidatableMixin
        self.assertTrue(hasattr(item_image, 'get_validators'))
        
        # Should have full_clean method enhanced by ValidatableMixin
        self.assertTrue(hasattr(item_image, 'full_clean'))
    
    def test_version_increment_on_update(self):
        """Test optimistic locking version increment"""
        item_image = ItemImage.objects.create(
            item=self.item,
            image=self._create_test_image(),
            caption='Original caption',
            created_by=self.user,
            updated_by=self.user
        )
        
        original_version = item_image.version
        
        # Update the image
        item_image.caption = 'Updated caption'
        item_image.save()
        
        # Version should increment
        self.assertEqual(item_image.version, original_version + 1)


class ItemImageQueryTest(TestImageFileMixin, TestCase):
    """Test case for ItemImage querying and relationships"""
    
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
        
        self.item1 = ItemSKU.objects.create(
            sku_code='TEST-001',
            name='Test Item 1',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.item2 = ItemSKU.objects.create(
            sku_code='TEST-002',
            name='Test Item 2',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # Use DRAFT status
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
    def test_item_images_relationship(self):
        """Test reverse relationship from Item to Images"""
        # Create images for item1
        image1 = ItemImage.objects.create(
            item=self.item1,
            image=self._create_test_image('image1.jpg'),
            created_by=self.user,
            updated_by=self.user
        )
        
        image2 = ItemImage.objects.create(
            item=self.item1,
            image=self._create_test_image('image2.jpg'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Test reverse relationship
        item_images = self.item1.images.all()
        self.assertEqual(item_images.count(), 2)
        self.assertIn(image1, item_images)
        self.assertIn(image2, item_images)
        
        # item2 should have no images
        self.assertEqual(self.item2.images.count(), 0)
    
    def test_ordering(self):
        """Test that images are ordered correctly"""
        # Create images with different primary status and dates
        image1 = ItemImage.objects.create(
            item=self.item1,
            image=self._create_test_image('image1.jpg'),
            is_primary=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        image2 = ItemImage.objects.create(
            item=self.item1,
            image=self._create_test_image('image2.jpg'),
            is_primary=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get ordered images
        images = list(self.item1.images.all())
        
        # Primary image should come first
        self.assertEqual(images[0], image2)  # Primary
        self.assertEqual(images[1], image1)  # Non-primary
