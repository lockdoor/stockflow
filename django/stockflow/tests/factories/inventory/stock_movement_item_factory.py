import factory

from tests.factories.user import AdminFactory
from tests.factories.catalog import ItemFactory
from . import stock_movement_factory

from inventory.models import StockMovementItem


class StockMovementItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockMovementItem

    # Core fields
    item_sku = factory.SubFactory(ItemFactory)
    quantity = factory.Faker("random_int", min=1, max=100)
    stock_movement = factory.SubFactory(stock_movement_factory.StockMovementFactory)
    lot_number = factory.Faker("uuid4")
    movement_type = StockMovementItem.MovementType.IN

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)