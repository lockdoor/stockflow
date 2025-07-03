from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class ItemBOMViewsTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        
    def test_item_autocomplete_view_requires_login(self):
        # Test that the autocomplete view requires login
        self.client.logout()
        response = self.client.get(reverse("catalog:item-bom-autocomplete"), {'q': 'test', 'category': '1'})
        self.assertEqual(response.status_code, 302)

    def test_item_autocomplete_view(self):
        # Test the autocomplete view for item BOM
        response = self.client.get(reverse("catalog:item-bom-autocomplete"), {'q': 'test', 'category': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/bom/partials/bom-autocomplete-list.html')
        self.assertIn('items', response.context)
        
    
    