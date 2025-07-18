from django import forms
from catalog.models.item import ItemSKU
from catalog.models.category import Category

class ItemForm(forms.ModelForm):
    """
    Form for creating and updating ItemSKU instances.
    Form validation is minimal as business logic validation is handled at the model level.
    """
    # Override category field to use only active categories
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.Select(),
        required=False,
        label="Category",
        help_text="Select a category for this item (optional)"
    )

    class Meta:
        model = ItemSKU
        fields = ['sku_code', 'name', 'unit', 'type', 'status', 'note', 'category']
        widgets = {
            'sku_code': forms.TextInput(attrs={
                'placeholder': 'Enter unique SKU code'
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter item name'
            }),
            'unit': forms.TextInput(attrs={
                'placeholder': 'Enter unit (e.g., pcs, kg, m)'
            }),
            'type': forms.Select(),
            'status': forms.Select(),
            'note': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter additional notes (optional)'
            }),
        }
        labels = {
            'sku_code': 'SKU Code',
            'name': 'Item Name',
            'unit': 'Unit of Measurement',
            'type': 'Item Type',
            'status': 'Status',
            'note': 'Additional Notes',
            'category': 'Category',
        }
        help_texts = {
            'sku_code': 'Unique identifier for the item',
            'name': 'Name of the item',
            'unit': 'Unit of measurement for this item (e.g., pcs, kg, m)',
            'type': 'Type of item - cannot be changed once set',
            'status': 'Current status of the item',
            'note': 'Additional notes about the item (optional)',
            'category': 'Select a category for this item (optional)',
        }
