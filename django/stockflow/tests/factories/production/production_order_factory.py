import factory
from production.models.production_order import ProductionOrder
from tests.factories.inventory.warehouse_factory import WarehouseFactory
from tests.factories.user import AdminFactory

class ProductionOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionOrder

    # Core fields
    warehouse = factory.SubFactory(WarehouseFactory)

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)
    