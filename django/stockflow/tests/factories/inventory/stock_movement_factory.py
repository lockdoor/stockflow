import factory

from inventory.models import StockMovement

from . import warehouse_factory
from tests.factories.user import AdminFactory

class StockMovementFactory(factory.django.DjangoModelFactory):
    """Factory for creating StockMovement instances."""
    
    class Meta:
        model = StockMovement
        
    # Core fields
    warehouse = factory.SubFactory(warehouse_factory.WarehouseFactory)
    reference_type = StockMovement.ReferenceType.NONE

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)