from django import forms
from production.models.production_order_bom import ItemSKU, ProductionOrderBOM

class ProductionOrderBOMForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)
        if production_order is not None:
            self.instance.production_order = production_order
        # query ItemSKU by active and type product
        self.fields['item_sku'].queryset = ItemSKU.objects.filter(status=ItemSKU.Status.ACTIVE, type=ItemSKU.Type.PRODUCT)

    class Meta:
        model = ProductionOrderBOM
        fields = [
            'item_sku',
            'planned_quantity',
            'note',
        ]
        widgets = {
            'item_sku': forms.Select(attrs={'class': 'form-control'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }
