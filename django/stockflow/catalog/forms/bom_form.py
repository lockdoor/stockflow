from django import forms
from catalog.models.bom import BOM

class BOMForm(forms.ModelForm):
    class Meta:
        model = BOM
        fields = ['quantity', 'component_sku', 'parent_sku']
        widgets = {
            'quantity': forms.NumberInput(),
            'component_sku': forms.HiddenInput(),
            'parent_sku': forms.HiddenInput(),
        }
        labels = {
            'quantity': 'quantity',
            'component_sku': 'Component',
        }
    
    def clean(self):
        component_sku = self.cleaned_data.get('component_sku')
        if not component_sku:
            raise forms.ValidationError("Component SKU is required.")
        parent_sku = self.cleaned_data.get('parent_sku')  
        if not parent_sku:
            raise forms.ValidationError("Parent SKU is required.")
        if component_sku == parent_sku:
            raise forms.ValidationError("Component SKU cannot be the same as Parent SKU.")