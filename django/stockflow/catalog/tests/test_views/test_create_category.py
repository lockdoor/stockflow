from django.test import TestCase
from django.contrib.auth.models import User, Permission
from catalog.forms.create_category_form import CreateCategoryForm

class CreateCategoryViewTest(TestCase):
    def setUp(self):
        self.URL = '/catalog/create_category'
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')
        self.permission = Permission.objects.get(codename='add_category')
        self.permission_item = Permission.objects.get(codename='add_itemsku')
        self.default_next_url = '/catalog/categories'

    def test_create_category_view_requires_login(self):
        """
        Test that the create category view requires login.
        """
        self.client.logout()  # Ensure the user is logged out
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)

    def test_create_category_view_without_permission(self):
        """
        Test that the create category view returns a 403 status code
        when the user does not have permission to add categories.
        """
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 403)

    def test_create_category_view_with_permission(self):
        """
        Test that the create category view returns a 200 status code
        when the user has permission to add categories.
        """
        self.user.user_permissions.add(self.permission)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/create_category.html')

    def test_create_category_view_has_form(self):
        """
        Test that the create category view has a form in the context.
        """
        self.user.user_permissions.add(self.permission)
        response = self.client.get(self.URL)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CreateCategoryForm)

    def test_create_category_view_form_invalid_submission(self):
        """
        Test that the create category view handles invalid form submission.
        """
        self.user.user_permissions.add(self.permission)
        response = self.client.post(self.URL, {'name': '', 'description': 'Test description'})
        self.assertEqual(response.status_code, 200)
        # check response is same page
        self.assertTemplateUsed(response, 'catalog/create_category.html')
        # check response is same url
        self.assertEqual(response.request['PATH_INFO'], self.URL)

    def test_create_category_view_form_valid_submission(self):
        """
        Test that the create category view handles valid form submission.
        """
        self.user.user_permissions.add(self.permission)
        form_data = {
            'name': 'New Category',
            'description': 'This is a new category.'
        }
        response = self.client.post(self.URL, form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.default_next_url)

    def test_create_category_view_redirects_to_next_url(self):
        """
        Test that the create category view redirects to the next URL
        after successful form submission.
        """
        self.user.user_permissions.add(self.permission)
        # Add permission to create raw item
        self.user.user_permissions.add(self.permission_item)
        next_url = '/catalog/create_raw_item'
        url = f'{self.URL}?next={next_url}'
        form_data = {
            'name': 'New Category',
            'description': 'This is a new category.',
        }
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, next_url)