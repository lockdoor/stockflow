from django import forms
from catalog.models.bom import BOM

class BOMForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extract parent_sku from kwargs if provided
        self.parent_sku = kwargs.pop('parent_sku', None)
        super().__init__(*args, **kwargs)
        
        # If parent_sku is provided, set it on the instance
        if self.parent_sku and not self.instance.pk:
            self.instance.parent_sku = self.parent_sku
    
    class Meta:
        model = BOM
        fields = ['quantity', 'component_sku']
        widgets = {
            'quantity': forms.NumberInput(),
            'component_sku': forms.TextInput(attrs={'placeholder': 'Component SKU', 'autocomplete': 'off'}),
        }
        labels = {
            'quantity': 'Quantity',
            'component_sku': 'Component',
        }
