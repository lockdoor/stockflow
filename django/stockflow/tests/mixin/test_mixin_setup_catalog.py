import random
from django.test import TestCase
from . import MixinSetupUser

from ..factories.catalog import CategoryFactory, ItemFactory, ProductFactory
from catalog.models import Category, ItemSKU

class MixinSetupCatalog(MixinSetupUser):

    catalog_categories_name: list[str] = ['Electronics', 'Clothing', 'Books']
    catalog_categories: list[Category] = []
    catalog_items: list[ItemSKU] = []
    catalog_products: list[ItemSKU] = []
    catalog_item_number = 10
    catalog_product_number = 3
    catalog_min_item_bom = 2
    catalog_max_item_bom = 3

    def setUp(self):
        super().setUp()
        # Set up additional test data for catalog tests
        for name in self.catalog_categories_name:
            self.catalog_categories.append(
                CategoryFactory(name=name, created_by=self.admin_user))

        for i in range(1, self.catalog_item_number + 1):
            self.catalog_items.append(
                ItemFactory(
                    name=f"Item {i}", 
                    created_by=self.admin_user, 
                    category=self.catalog_categories[i % len(self.catalog_categories)]))

        for i in range(1, self.catalog_product_number + 1):
            number_of_items = random.randint(self.catalog_min_item_bom, self.catalog_max_item_bom)
            bom_items = random.sample(self.catalog_items, number_of_items)
            product = ProductFactory(
                name=f"Product {i}", 
                created_by=self.admin_user, 
                category=self.catalog_categories[i % len(self.catalog_categories)], 
                bom=bom_items
            )
            self.catalog_products.append(product)

class MyCatalogTests(MixinSetupCatalog, TestCase):

    catalog_item_number = 12
    catalog_product_number = 5
    catalog_min_item_bom = 2
    catalog_max_item_bom = 4
    
    def test_catalog_setup(self):
        self.assertEqual(len(self.catalog_categories), len(self.catalog_categories_name))
        self.assertEqual(len(self.catalog_items), self.catalog_item_number)
        self.assertEqual(len(self.catalog_products), self.catalog_product_number)
        for product in self.catalog_products:
            self.assertTrue(product.bom_count >= self.catalog_min_item_bom and product.bom_count <= self.catalog_max_item_bom)
