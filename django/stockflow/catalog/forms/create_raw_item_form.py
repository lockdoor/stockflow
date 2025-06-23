from django import forms
from catalog.models.item import ItemSKU
from catalog.models.category import Category

# class CreateRawItemForm(forms.ModelForm):
#     new_category = forms.CharField(
#         required=False,
#         label="New Category",
#         widget=forms.TextInput(attrs={'class': 'form-control'}),
#         help_text="Leave blank if using existing category."
#     )

#     class Meta:
#         model = ItemSKU
#         fields = [
#             'sku_code',
#             'name',
#             'unit',
#             'status',
#             'description',
#             'category',
#         ]
#         widgets = {
#             'sku_code': forms.TextInput(attrs={'class': 'form-control'}),
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'unit': forms.TextInput(attrs={'class': 'form-control'}),
#             'status': forms.Select(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         new_cat = cleaned_data.get("new_category")
#         category = cleaned_data.get("category")

#         if new_cat and category:
#             raise forms.ValidationError("Please either select a category or enter a new one, not both.")

#         return cleaned_data

#     def save(self, commit=True):
#         new_cat_name = self.cleaned_data.get('new_category')
#         if new_cat_name:
#             category, _ = Category.objects.get_or_create(name=new_cat_name)
#             self.instance.category = category
#         return super().save(commit)

class CreateRawItemForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = ItemSKU
        fields = ['sku_code', 'name', 'unit', 'status', 'description', 'category']
        widgets = {
            'sku_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
