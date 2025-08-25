import factory
from ..user import AdminFactory
from . import ItemFactory
from catalog.models import BOM
from catalog.models import ItemSKU

class BOMFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BOM

    # Core fields
    parent_sku = factory.SubFactory(ItemFactory, type=ItemSKU.Type.PRODUCT)
    component_sku = factory.SubFactory(ItemFactory)
    quantity = factory.Faker('random_int', min=1, max=100)

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)
