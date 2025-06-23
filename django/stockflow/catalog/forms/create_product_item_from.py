from django import forms
from catalog.models.item import ItemSKU
from catalog.models.bom import BOM

class CreateProductItemForm(forms.ModelForm):
    class Meta:
        model = ItemSKU
        fields = [
            'sku_code',
            'name',
            'unit',
            'type',
            'status',
            'description'
        ]
        widgets = {
            'sku_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }