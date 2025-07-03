from django.core.management.base import BaseCommand
from catalog.models.category import Category
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU, ItemSKUType, ItemSKUStatus
from faker import Faker
import random

class Command(BaseCommand):
    help = "Seed 20 sample items"

    def handle(self, *args, **options):
        fake = Faker()
        user = User.objects.get(id=1)  # ID 1 is superuser by default
        categories = Category.objects.all()
        
        # create 20 active RAW MATERIALS items
        for _ in range(1, 21):
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=ItemSKUType.RAW,
                status=ItemSKUStatus.ACTIVE,
                created_by=user,
                updated_by=user,
                description=fake.sentence(),
                category=random.choice(categories),
            )
            
        # create 10 active FINISHED PRODUCTS items
        for _ in range(1, 11):
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-FINISHED-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=ItemSKUType.PRODUCT,
                status=ItemSKUStatus.ACTIVE,
                created_by=user,
                updated_by=user,
                description=fake.sentence(),
                category=random.choice(categories),
            )
            
        # create 5 active PACKAGING MATERIALS items
        for _ in range(1, 6):
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-PACKAGE-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=ItemSKUType.PACKAGE,
                status=ItemSKUStatus.ACTIVE,
                created_by=user,
                updated_by=user,
                description=fake.sentence(),
                category=random.choice(categories),
            )
        self.stdout.write(self.style.SUCCESS("Successfully created sample items."))