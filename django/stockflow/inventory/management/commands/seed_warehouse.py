from django.core.management.base import BaseCommand
from inventory.models.warehouse import Warehouse
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seed the 2 warehouse with initial data'

    def handle(self, *args, **kwargs):
        user = User.objects.get(id=1) # ID 1 is superuser by default
        
        # Create first warehouse instance
        warehouse1 = Warehouse.objects.create(
            name='Main Warehouse',
            address='123 Main St',
            note='Central storage for all inventory',
            is_active=True,
            created_by=user,
            updated_by=user
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created warehouse: {warehouse1.name}'))
        
        # Create second warehouse instance
        warehouse2 = Warehouse.objects.create(
            name='Secondary Warehouse',
            address='456 Secondary St',
            note='Backup storage for overflow inventory',
            is_active=True,
            created_by=user,
            updated_by=user
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created warehouse: {warehouse2.name}'))
        