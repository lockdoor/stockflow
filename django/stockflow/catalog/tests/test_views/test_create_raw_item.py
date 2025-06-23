from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
# forms
from catalog.forms.create_raw_item_form import CreateRawItemForm
# models
from catalog.models.category import Category
from catalog.models.item import ItemSKU

class CreateRawItemViewTest(TestCase):
    def setUp(self):
        self.URL = '/catalog/create_raw_item'
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')
        self.permission = Permission.objects.get(codename='add_itemsku')
        # self.permission_category = Permission.objects.get(codename='add_category')
        self.user.user_permissions.add(self.permission)
        self.category = Category.objects.create(
            name='Test Category',
            description='This is a test category.',
            created_by=self.user,
            updated_by=self.user,
        )
        self.default_next_url = '/catalog/items'  # Default next URL after creation
    
    def test_create_raw_item_view_requires_login(self):
        """
        Test that the create raw item view requires login.
        """
        self.client.logout()  # Ensure the user is logged out
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)
    
    def test_create_raw_item_view_without_permission(self):
        """
        Test that the create raw item view returns a 403 status code
        when the user does not have permission to add items.
        """
        # Remove the permission from the user
        self.user.user_permissions.remove(self.permission)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 403)

    def test_create_raw_item_view_with_permission(self):
        """
        Test that the create raw item view returns a 200 status code
        when the user has permission to add items.
        """
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/create_raw_item.html')
        self.assertEqual(response.request['PATH_INFO'], self.URL)
    
    def test_create_raw_item_view_has_form(self):
        """
        Test that the create raw item view has a form in the context.
        """
        response = self.client.get(self.URL)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CreateRawItemForm)

    def test_create_raw_item_view_form_invalid_submission(self):
        """
        Test that the create raw item view handles invalid form submission.
        """
        response = self.client.post(self.URL, {
            'sku_code': '', 
            'name': 'Test Item', 
            'unit': 'pcs', 
            'status': 'available', 
            'description': 'This is a test item.', 
            'category': 1})
        # check response is same page
        self.assertTemplateUsed(response, 'catalog/create_raw_item.html')
        # check response is same url
        self.assertEqual(response.request['PATH_INFO'], self.URL)

    def test_create_raw_item_view_form_valid_submission(self):
        """
        Test that the create raw item view handles valid form submission.
        """
        form_data = {
            'sku_code': 'TEST123',
            'name': 'Test Item',
            'unit': 'pcs',
            'status': 'ACTIVE',
            # 'description': 'This is a test item.',
            # 'category': 1
        }
        response = self.client.post(self.URL, form_data)        
        # Check that the item was created
        item = ItemSKU.objects.get(sku_code='TEST123')
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.unit, 'pcs')
        self.assertEqual(item.status, 'ACTIVE')
        # self.assertEqual(item.description, 'This is a test item.')
        # self.assertEqual(item.category, self.category)
        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.default_next_url)

    def test_create_raw_item_view_form_valid_submission_full_field(self):
        """
        Test that the create raw item view handles valid form submission full field.
        """
        form_data = {
            'sku_code': 'TEST1234',
            'name': 'Test Item 2',
            'unit': 'pcs',
            'status': 'ACTIVE',
            'description': 'This is a test item.',
            'category': self.category.id  # Use existing category
        }
        response = self.client.post(self.URL, form_data)        
        # Check that the item was created
        item = ItemSKU.objects.get(sku_code='TEST1234')
        self.assertEqual(item.name, 'Test Item 2')
        self.assertEqual(item.unit, 'pcs')
        self.assertEqual(item.status, 'ACTIVE')
        self.assertEqual(item.description, 'This is a test item.')
        self.assertEqual(item.category, self.category)
        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.default_next_url)
