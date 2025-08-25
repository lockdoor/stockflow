import factory
from inventory.models import Warehouse
from tests.factories.user import AdminFactory

class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    # Core fields
    name = factory.Sequence(lambda n: f"Warehouse {n}")
    code = factory.Sequence(lambda n: f"WH{n:03}")

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)