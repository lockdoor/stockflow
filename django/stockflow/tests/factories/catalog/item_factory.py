import factory
from ..user import AdminFactory
from catalog.models import ItemSKU

class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemSKU

    # Core fields
    name = factory.Sequence(lambda n: f"item_{n}")
    sku_code = factory.Faker('ean13')
    unit = factory.Faker('word')

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)