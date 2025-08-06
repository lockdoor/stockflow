"""
Stock Movement Form

Form for creating and editing stock movements with clean validation.
UI styling handled via widget_tweaks in templates.

Author: StockFlow Team
Created: 2025
"""

from django import forms
from inventory.models.stock_movement import StockMovement
from inventory.models.warehouse import Warehouse


class StockMovementForm(forms.ModelForm):
    """Form for creating and editing stock movements"""
    
    class Meta:
        model = StockMovement
        fields = [
            'warehouse',
            'reference_type',
            'reference_id',
            'note',
        ]
        widgets = {
            'warehouse': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_id': forms.NumberInput(attrs={
                'placeholder': 'Enter reference ID (optional)',
                'min': '1',
                'class': 'form-control'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Additional notes about this stock movement (optional)',
                'rows': 3,
                'maxlength': '1000',
                'class': 'form-control'
            }),
        }
        
        labels = {
            'warehouse': 'Warehouse',
            'reference_type': 'Reference Type',
            'reference_id': 'Reference ID',
            'note': 'Notes',
        }
        
        help_texts = {
            'warehouse': 'Select the warehouse where this stock movement occurs',
            'reference_type': 'Select the type of document this movement references',
            'reference_id': 'ID of the referenced document (required for most reference types)',
            'note': 'Additional information about this stock movement (optional, max 1000 characters)',
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom logic"""
        super().__init__(*args, **kwargs)
        
        # Limit warehouse choices to active warehouses only
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        
        # Set initial reference type to NONE for new movements
        if not self.instance.pk:
            self.fields['reference_type'].initial = StockMovement.ReferenceType.NONE
        
        # Make reference_id conditionally required based on reference_type
        self.fields['reference_id'].required = False
    
    def clean_note(self):
        """Validate and normalize note field"""
        note = self.cleaned_data.get('note')
        if note:
            # Strip whitespace and normalize
            note = note.strip()
            # Return None if note becomes empty after stripping
            if not note:
                return None
        else:
            # Return None for empty/None input
            return None
        return note
