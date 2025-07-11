from django import forms
from inventory.models.stock_movement import StockMovement, StockMovementReferenceType, StockMovementStatus
from inventory.models.warehouse import Warehouse

class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = [
            'reference_type',
            'reference_id',
            'note',
            'warehouse',
            'status',
        ]
        widgets = {
            'reference_type': forms.Select(attrs={'class': 'form-select'}),
            'reference_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'warehouse': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
