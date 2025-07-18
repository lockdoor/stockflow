from django.core.management.base import BaseCommand
from catalog.models.category import Category
from django.contrib.auth.models import User
from catalog.models.item import ItemSKU
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
                type=ItemSKU.Type.RAW,
                status=ItemSKU.Status.ACTIVE,
                created_by=user,
                updated_by=user,
                note=fake.sentence(),
                category=random.choice(categories),
            )
            
        # create 10 active FINISHED PRODUCTS items
        for _ in range(1, 11):
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-FINISHED-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=ItemSKU.Type.PRODUCT,
                status=ItemSKU.Status.DRAFT,
                created_by=user,
                updated_by=user,
                note=fake.sentence(),
                category=random.choice(categories),
            )
            
        # create 5 active PACKAGING MATERIALS items
        for _ in range(1, 6):
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-PACKAGE-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=ItemSKU.Type.PACKAGE,
                status=ItemSKU.Status.DRAFT,
                created_by=user,
                updated_by=user,
                note=fake.sentence(),
                category=random.choice(categories),
            )
        # create 3 inactive items (mixed types)
        for _ in range(1, 4):
            item_type = random.choice([ItemSKU.Type.RAW, ItemSKU.Type.PRODUCT, ItemSKU.Type.PACKAGE])
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-INACTIVE-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=item_type,
                status=ItemSKU.Status.INACTIVE,
                created_by=user,
                updated_by=user,
                note=fake.sentence(),
                category=random.choice(categories),
            )
            
        # create a few active products (those that have been "locked")
        for _ in range(1, 6):
            ItemSKU.objects.create(
                sku_code=fake.unique.bothify("SKU-ACTIVE-PROD-####"),
                name=fake.word().title(),
                unit=random.choice(["kg", "pcs", "m"]),
                type=ItemSKU.Type.PRODUCT,
                status=ItemSKU.Status.ACTIVE,  # These products have been "locked"
                created_by=user,
                updated_by=user,
                note=fake.sentence(),
                category=random.choice(categories),
            )
            
        self.stdout.write(self.style.SUCCESS("Successfully created sample items."))