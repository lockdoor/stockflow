import factory
import uuid
from ..user import AdminFactory
from . import CategoryFactory
from catalog.models import ItemSKU

class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemSKU

    # Core fields
    name = factory.Sequence(lambda n: f"item_{n}")
    sku_code = factory.LazyFunction(lambda: f"ITEM-{str(uuid.uuid4())[:8]}")  # Thread-safe unique SKU
    unit = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)