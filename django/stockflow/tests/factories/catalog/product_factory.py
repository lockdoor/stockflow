import factory
import uuid
from ..user import AdminFactory
from . import BOMFactory
from . import ItemFactory

from catalog.models import ItemSKU

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemSKU

    # Core fields
    sku_code = factory.LazyFunction(lambda: f"PROD-{str(uuid.uuid4())[:8]}")  # Thread-safe unique SKU
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
            # Create unique components to avoid circular reference
            unique_id = str(uuid.uuid4())[:8]  # Thread-safe unique identifier
            default_components = []
            for i in range(bom_count):
                component = ItemFactory(
                    sku_code=f"COMP-{unique_id}-{i}",
                    name=f"Component for {self.name} #{i+1}",
                    created_by=self.created_by, 
                    updated_by=self.updated_by
                )
                default_components.append(component)
            
            for component in default_components:
                BOMFactory(parent_sku=self, component_sku=component)

        self.status = ItemSKU.Status.ACTIVE
        self.save()

