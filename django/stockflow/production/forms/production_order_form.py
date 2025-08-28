"""
Production Order Form

Form for creating and editing production orders with clean validation.
UI styling handled via widget_tweaks in templates.

Author: StockFlow Team
Created: 2025
"""

from django import forms
from production.models.production_order import ProductionOrder
from inventory.models.warehouse import Warehouse

class ProductionOrderForm(forms.ModelForm):
    """Form for creating and editing production orders"""
    class Meta:
        model = ProductionOrder
        fields = [
            'warehouse',
            'note'
        ]
        widgets = {
            'warehouse': forms.Select(attrs={
                'class': 'form-select'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Optional notes about this production order',
                'rows': 3,
                'maxlength': '1000',
                'class': 'form-control'
            }),
        }
        labels = {
            'warehouse': 'Warehouse',
            'note': 'Notes',
        }
        help_texts = {
            'warehouse': 'Select the warehouse for this production order',
            'note': 'Additional information about this production order (optional, max 1000 characters)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit warehouse choices to active warehouses only
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)

    def clean_note(self):
        """Validate and normalize note field"""
        note: str | None = self.cleaned_data.get('note')
        # if note:
        #     note = note.strip()
        #     if not note:
        #         return None
        # else:
        #     return None
        
        if note is None:
            return ''
        return note.strip()
