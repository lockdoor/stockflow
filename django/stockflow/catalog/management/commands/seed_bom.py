from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
# models
from catalog.models.item import ItemSKU, ItemSKUType, ItemSKUStatus
from catalog.models.bom import BOM
# from faker import Faker
import random

class Command(BaseCommand):
    help = "Seed 5 component items for BOMs"

    def handle(self, *args, **options):
        # fake = Faker()
        user = User.objects.get(id=1)  # ID 1 is superuser by default
        parent_item = ItemSKU.objects.filter(type=ItemSKUType.PRODUCT, status=ItemSKUStatus.ACTIVE).last()
        
        if not parent_item:
            self.stdout.write(self.style.ERROR("No parent items found. Please create some parent items first."))
            return
        
        component_items = ItemSKU.objects.filter(type=ItemSKUType.RAW, status=ItemSKUStatus.ACTIVE)[:5]
            
        # create 5 component items
        for component in component_items:
            BOM.objects.create(
                parent_sku=parent_item,
                component_sku=component,
                quantity=random.randint(1, 10),
                created_by=user,
                updated_by=user,
            )
        
        
        