from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models.category import Category

class CategoryViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.staff = User.objects.create_user(username="staff", password="pass1234")
        self.staff.user_permissions.add(Permission.objects.get(codename='add_category'))
        self.staff.user_permissions.add(Permission.objects.get(codename='change_category'))

        self.category = Category.objects.create(
            name="Electronics",
            description="Gadgets and devices",
            created_by=self.staff,
            updated_by=self.staff,
        )

    # list
    def test_list_requires_login(self):
        response = self.client.get(reverse("catalog:category-list"))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_list_as_authenticated_user(self):
        self.client.login(username="tester", password="pass1234")
        response = self.client.get(reverse("catalog:category-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Electronics")

    # create
    def test_create_category_requires_login(self):
        response = self.client.get(reverse("catalog:category-create"))
        self.assertEqual(response.status_code, 302)
    
    def test_create_category_requires_permission(self):
        self.client.login(username="tester", password="pass1234")
        response = self.client.post(reverse("catalog:category-create"), {
            'name': 'Books',
            'description': 'All about books',
        })
        self.assertEqual(response.status_code, 403)

    def test_create_category_success(self):
        self.client.login(username="staff", password="pass1234")
        response = self.client.post(reverse("catalog:category-create"), {
            'name': 'Books',
            'description': 'All about books',
        }, HTTP_HX_REQUEST='true')  # simulate HTMX
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Category.objects.filter(name='Books').exists())

    def test_create_invalid_form_returns_form(self):
        self.client.login(username="staff", password="pass1234")
        response = self.client.post(reverse("catalog:category-create"), {
            'name': '',  # Invalid
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    # edit
    def test_edit_category_requires_login(self):
        response = self.client.get(reverse("catalog:category-edit", args=[self.category.id]))
        self.assertEqual(response.status_code, 302)
        
    def test_edit_category_requires_permission(self):
        self.client.login(username="tester", password="pass1234")
        response = self.client.post(
            reverse("catalog:category-edit", args=[self.category.id]),
            {'name': 'Updated Name', 'description': 'Updated',}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_edit_category_success(self):
        self.client.login(username="staff", password="pass1234")
        response = self.client.post(
            reverse("catalog:category-edit", args=[self.category.id]),
            {'name': 'Updated Name', 'description': 'Updated',},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Name')

    # detail
    def test_detail_view_requires_login(self):
        response = self.client.get(reverse("catalog:category-detail", args=[self.category.id]))
        self.assertEqual(response.status_code, 302)

    def test_detail_view_success(self):
        self.client.login(username="tester", password="pass1234")
        response = self.client.get(reverse("catalog:category-detail", args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Electronics")
