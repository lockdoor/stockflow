from django import forms
from inventory.models.stock_movement_item import StockMovementItem

class StockMovementItemForm(forms.ModelForm):
    class Meta:
        model = StockMovementItem
        fields = [
            'stock_movement',
            'item',
            'movement_type',
            'quantity',
            'lot',
            'expired',
            'note',
        ]
        widgets = {
            'stock_movement': forms.HiddenInput(),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'lot': forms.TextInput(attrs={'class': 'form-control'}),
            'expired': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
