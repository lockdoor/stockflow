from django.core.management.base import BaseCommand
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seed the stock movements with initial data'

    def handle(self, *args, **kwargs):
        user = User.objects.get(id=1)  # ID 1 is superuser by default
        
        # Create stock movement for Main Warehouse
        warehouse = Warehouse.objects.filter().first()
        stock_movement = StockMovement.objects.create(
            warehouse=warehouse,
            note='Initial stock movement',
            created_by=user,
            updated_by=user,
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created stock movement: {stock_movement} in {warehouse.name}'))
        