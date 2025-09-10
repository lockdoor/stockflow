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
    
    @factory.post_generation
    def ensure_relationships_saved(self, create, extracted, **kwargs):
        """Ensure all related objects are properly saved before validation"""
        if not create:
            return
        
        # Make sure production_order is saved
        if hasattr(self.production_order, 'pk') and not self.production_order.pk:
            self.production_order.save()
            
        # Make sure item_sku is saved
        if hasattr(self.item_sku, 'pk') and not self.item_sku.pk:
            self.item_sku.save()
