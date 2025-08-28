import factory
from ..user import AdminFactory
from . import BOMFactory
from . import ItemFactory

from catalog.models import ItemSKU

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemSKU

    # Core fields
    sku_code = factory.Faker('ean13')
    name = factory.Sequence(lambda n: f"product_{n}")
    type = ItemSKU.Type.PRODUCT
    status = ItemSKU.Status.DRAFT
    unit = factory.Faker('word')
    
    # Audit fields
    created_by = factory.SubFactory(AdminFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)

    @factory.post_generation
    def bom(self, create, extracted: list[ItemSKU], **kwargs):
        if not create:
            return

        # รับจำนวน bom จาก kwargs ถ้าไม่กำหนดใช้ค่า default = 3
        # use case:
        # product: ItemSKU = ProductFactory(bom__bom_count=5)
        bom_count = kwargs.get('bom_count', getattr(self, 'bom_count', 3))

        if extracted:
            for component in extracted:
                BOMFactory(parent_sku=self, component_sku=component)
        else:
            default_components = ItemFactory.create_batch(bom_count, created_by=self.created_by, updated_by=self.updated_by)
            for component in default_components:
                BOMFactory(parent_sku=self, component_sku=component)

        self.status = ItemSKU.Status.ACTIVE
        self.save()

