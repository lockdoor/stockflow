from django.core.management.base import BaseCommand
from catalog.models.category import Category
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Seed 10 sample categories"
    
    CATEGORIES = [
        "Raw Materials",
        "Work In Progress (WIP)",
        "Finished Goods",
        "Packaging Materials",
        "Spare Parts",
        "Maintenance Supplies",
        "Tools & Equipment",
        "Consumables",
        "Quality Control Materials",
        "Office Supplies",
    ]
    
    def handle(self, *args, **options):
        user = User.objects.get(id=1) # ID 1 is superuser by default
        for i in self.CATEGORIES:
            Category.objects.create(
                name=i, 
                description=f"Description for {i}", 
                created_by= user,
                updated_by= user,
            )
        self.stdout.write(self.style.SUCCESS(f"Successfully created  categories."))
