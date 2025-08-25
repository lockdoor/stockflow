import factory
from ..user import AdminFactory

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'catalog.Category'

    # Core fields
    name = factory.Sequence(lambda n: f"category_{n}")

    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)