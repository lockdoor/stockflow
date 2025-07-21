from django.core.management.base import BaseCommand
from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_item import StockMovementItem
from catalog.models.item import ItemSKU
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seed the stock items movements with initial data'

    def handle(self, *args, **kwargs):
        user = User.objects.get(id=1)  # ID 1 is superuser by default
        
        stock_movement = StockMovement.objects.filter().first()
        items = ItemSKU.objects.filter(status=ItemSKU.Status.ACTIVE).order_by('id')[:5]
        for item in items:
            StockMovementItem.objects.create(
                stock_movement=stock_movement,
                item_sku=item,
                quantity=10,  # Example quantity
                created_by=user,
                updated_by=user,
                movement_type=StockMovementItem.MovementType.IN,
                note=f"Initial stock for {item.sku_code}",
                lot_number=f"LOT-{item.id}",
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully added item: {item.sku_code} to stock movement: {stock_movement.id}'))
        
        
