"""
Warehouse Form

Form for creating and editing warehouses with clean validation.
UI styling handled via widget_tweaks in templates.

Author: StockFlow Team
Created: 2025
"""

from django import forms
from inventory.models.warehouse import Warehouse


class WarehouseForm(forms.ModelForm):
    """Form for creating and editing warehouses"""
    
    class Meta:
        model = Warehouse
        fields = [
            'name',
            'code', 
            'address',
            'note',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter warehouse name (e.g., Main Warehouse)',
                'maxlength': '100'
            }),
            'code': forms.TextInput(attrs={
                'placeholder': 'Enter warehouse code (e.g., MAIN01)',
                'maxlength': '10',
                'style': 'text-transform: uppercase'
            }),
            'address': forms.Textarea(attrs={
                'placeholder': 'Enter warehouse address (optional)',
                'rows': 3,
                'maxlength': '500'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Additional notes (optional)',
                'rows': 2,
                'maxlength': '1000'
            }),
        }
        
        labels = {
            'name': 'Warehouse Name',
            'code': 'Warehouse Code',
            'address': 'Address',
            'note': 'Notes',
            'is_active': 'Active Status',
        }
        
        help_texts = {
            'name': 'Enter a descriptive name for the warehouse (2-100 characters)',
            'code': 'Unique code for the warehouse (2-10 alphanumeric characters)',
            'address': 'Physical address of the warehouse (optional, max 500 characters)',
            'note': 'Additional information about the warehouse (optional, max 1000 characters)',
            'is_active': 'Check to make this warehouse active for operations',
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom logic"""
        super().__init__(*args, **kwargs)
        
        # Set default active status for new warehouses
        if not self.instance.pk:
            self.fields['is_active'].initial = True
        
        # Make code field uppercase on client side
        self.fields['code'].widget.attrs.update({
            'oninput': 'this.value = this.value.toUpperCase()'
        })
    
    def clean_code(self):
        """Validate and normalize warehouse code"""
        code = self.cleaned_data.get('code')
        if code:
            # Normalize to uppercase and strip whitespace
            code = code.upper().strip()
        return code
