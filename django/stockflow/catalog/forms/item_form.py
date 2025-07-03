from django import forms
from catalog.models.item import ItemSKU
from catalog.models.category import Category

class ItemForm(forms.ModelForm):
    """
    Form for creating a new ItemSKU.
    """
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = ItemSKU
        fields = ['sku_code', 'name', 'unit', "type", "status", 'description', 'category']
        widgets = {
            'sku_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def clean_sku_code(self):
        sku_code = self.cleaned_data.get("sku_code")
        if self.instance.pk:
            old = ItemSKU.objects.get(pk=self.instance.pk)
            if sku_code != old.sku_code:
                raise forms.ValidationError("SKU code cannot be changed.")
        return sku_code
