import factory
from tests.factories.production import ProductionOrderFactory
# from tests.factories.catalog import ItemFactory
from tests.factories.catalog import ProductFactory
from tests.factories.user import AdminFactory

from production.models import ProductionOrderBOM

class ProductionOrderBOMFactory(factory.django.DjangoModelFactory):
    class Meta:
        model=ProductionOrderBOM
        
    #Core fields
    production_order=factory.SubFactory(ProductionOrderFactory)
    item_sku=factory.SubFactory(ProductFactory)
    planned_quantity=10
    
    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)
