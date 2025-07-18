from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from catalog.models.item import ItemSKU
from catalog.models.category import Category


class ItemUpdateViewTest(TestCase):
    """Test suite for the ItemUpdateView"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user with necessary permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Assign required permissions
        content_type = ContentType.objects.get_for_model(ItemSKU)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='change_itemsku'
        )
        self.user.user_permissions.add(permission)
        
        # Create user without permissions for testing permission checks
        self.unprivileged_user = User.objects.create_user(
            username='unprivileged',
            password='testpassword'
        )
        
        # Create an active category for testing
        self.active_category = Category.objects.create(
            name='Active Category',
            created_by=self.user,
            updated_by=self.user,
            is_active=True
        )
        
        # Create an inactive category for testing
        self.inactive_category = Category.objects.create(
            name='Inactive Category',
            created_by=self.user,
            updated_by=self.user,
            is_active=False
        )
        
        # Create test items for updating
        self.raw_item = ItemSKU.objects.create(
            sku_code='RAW-001',
            name='Raw Material Item',
            unit='kg',
            type=ItemSKU.Type.RAW,
            status=ItemSKU.Status.ACTIVE,  # RAW items must be ACTIVE
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.product_item = ItemSKU.objects.create(
            sku_code='PROD-001',
            name='Product Item',
            unit='pcs',
            type=ItemSKU.Type.PRODUCT,
            status=ItemSKU.Status.DRAFT,  # PRODUCT items can be in DRAFT
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.package_item = ItemSKU.objects.create(
            sku_code='PKG-001',
            name='Package Item',
            unit='set',
            type=ItemSKU.Type.PACKAGE,
            status=ItemSKU.Status.ACTIVE,  # PACKAGE items can be ACTIVE
            category=self.active_category,
            created_by=self.user,
            updated_by=self.user
        )
        
        # URLs for testing
        self.raw_item_url = reverse('catalog:item-edit', kwargs={'pk': self.raw_item.pk})
        self.product_item_url = reverse('catalog:item-edit', kwargs={'pk': self.product_item.pk})
        self.package_item_url = reverse('catalog:item-edit', kwargs={'pk': self.package_item.pk})
        
        # Valid update data
        self.valid_update_data = {
            'sku_code': 'PROD-001',  # Can't change SKU code
            'name': 'Updated Product Name',
            'unit': 'box',
            'type': ItemSKU.Type.PRODUCT,  # Can't change type
            'status': ItemSKU.Status.ACTIVE,
            'note': 'Updated notes',
            'category': self.active_category.id,
        }

    def test_login_required(self):
        """Test that login is required to access the view"""
        # Attempt to access without login
        response = self.client.get(self.raw_item_url)
        
        # Should redirect to login page (status code 302 is a redirect)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)
        
    def test_permission_required(self):
        """Test that proper permission is required"""
        # Log in as unprivileged user
        self.client.login(username='unprivileged', password='testpassword')
        
        # Attempt to access with login but without permission
        response = self.client.get(self.raw_item_url)
        
        # Should return forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_get_update_form(self):
        """Test that the view returns the correct form with item data"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Get the form
        response = self.client.get(self.product_item_url)
        
        # Should return success
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/item/partials/item-form.html')
        
        # Check that form is pre-filled with item data
        self.assertContains(response, 'Product Item')  # Item name
        self.assertContains(response, 'PROD-001')      # SKU code
    
    def test_update_item_success(self):
        """Test that an item can be updated successfully"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Post update data
        response = self.client.post(
            self.product_item_url, 
            self.valid_update_data, 
            HTTP_HX_REQUEST='true'
        )
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        
        # Verify item was updated in database
        self.product_item.refresh_from_db()
        self.assertEqual(self.product_item.name, 'Updated Product Name')
        self.assertEqual(self.product_item.unit, 'box')
        self.assertEqual(self.product_item.note, 'Updated notes')
        self.assertEqual(self.product_item.status, ItemSKU.Status.ACTIVE)
        self.assertEqual(self.product_item.updated_by, self.user)
    
    def test_attempt_to_change_sku_code(self):
        """Test that SKU code cannot be changed once set"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Create update data with changed SKU code
        invalid_data = self.valid_update_data.copy()
        invalid_data['sku_code'] = 'CHANGED-001'
        
        # Post invalid update
        response = self.client.post(
            self.product_item_url, 
            invalid_data, 
            HTTP_HX_REQUEST='true'
        )
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SKU code cannot be changed once set")
        
        # Verify item was not updated
        self.product_item.refresh_from_db()
        self.assertEqual(self.product_item.sku_code, 'PROD-001')  # Original SKU code
    
    def test_attempt_to_change_type(self):
        """Test that item type cannot be changed once set"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Create update data with changed type
        invalid_data = self.valid_update_data.copy()
        invalid_data['type'] = ItemSKU.Type.PACKAGE  # Try to change from PRODUCT to PACKAGE
        
        # Post invalid update
        response = self.client.post(
            self.product_item_url, 
            invalid_data, 
            HTTP_HX_REQUEST='true'
        )
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Item type cannot be changed once set")
        
        # Verify item was not updated
        self.product_item.refresh_from_db()
        self.assertEqual(self.product_item.type, ItemSKU.Type.PRODUCT)  # Original type
    
    def test_update_raw_item_to_draft(self):
        """Test that RAW items cannot be set to DRAFT status"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Create update data with DRAFT status for RAW item
        invalid_data = {
            'sku_code': 'RAW-001',
            'name': 'Updated Raw Name',
            'unit': 'g',
            'type': ItemSKU.Type.RAW,
            'status': ItemSKU.Status.DRAFT,  # Invalid for RAW items
            'note': 'Updated notes',
            'category': self.active_category.id,
        }
        
        # Post invalid update
        response = self.client.post(
            self.raw_item_url, 
            invalid_data, 
            HTTP_HX_REQUEST='true'
        )
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Raw materials cannot be in DRAFT status")
        
        # Verify item was not updated to DRAFT
        self.raw_item.refresh_from_db()
        self.assertEqual(self.raw_item.status, ItemSKU.Status.ACTIVE)  # Still ACTIVE
    
    def test_update_to_inactive_category(self):
        """Test that items cannot be assigned to inactive categories"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Create update data with inactive category
        invalid_data = self.valid_update_data.copy()
        invalid_data['category'] = self.inactive_category.id
        
        # Post invalid update
        response = self.client.post(
            self.product_item_url, 
            invalid_data, 
            HTTP_HX_REQUEST='true'
        )
        
        # Should return form with errors about invalid category
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid choice")  # Form validation message
        
        # Verify item category was not updated
        self.product_item.refresh_from_db()
        self.assertEqual(self.product_item.category.id, self.active_category.id)
    
    def test_update_with_missing_required_fields(self):
        """Test validation of required fields"""
        # Log in with privileged user
        self.client.login(username='testuser', password='testpassword')
        
        # Create update data with missing name
        invalid_data = self.valid_update_data.copy()
        invalid_data.pop('name')
        
        # Post invalid update
        response = self.client.post(
            self.product_item_url, 
            invalid_data, 
            HTTP_HX_REQUEST='true'
        )
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")
        
        # Verify item was not updated
        self.product_item.refresh_from_db()
        self.assertEqual(self.product_item.name, 'Product Item')  # Original name
