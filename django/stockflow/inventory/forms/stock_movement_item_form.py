"""
Stock Movement Item Form

Form for creating and editing stock movement items with clean validation.
UI styling handled via widget_tweaks in templates.

Author: StockFlow Team
Created: 2025
"""

from django import forms
from inventory.models.stock_movement_item import StockMovementItem
from catalog.models.item import ItemSKU


class StockMovementItemForm(forms.ModelForm):
    """Form for creating and editing stock movement items"""
    
    class Meta:
        model = StockMovementItem
        fields = [
            'stock_movement',
            'item_sku',
            'movement_type',
            'quantity',
            'lot_number',
            'expiry_date',
            'note',
        ]
        widgets = {
            'stock_movement': forms.HiddenInput(),
            'item_sku': forms.Select(attrs={
                'class': 'form-select'
            }),
            'movement_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Enter quantity',
                'min': '0.01',
                'step': '0.01',
                'class': 'form-control'
            }),
            'lot_number': forms.TextInput(attrs={
                'placeholder': 'Enter lot/batch number (optional)',
                'maxlength': '64',
                'class': 'form-control'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Additional notes for this item (optional)',
                'rows': 2,
                'maxlength': '500',
                'class': 'form-control'
            }),
        }
        
        labels = {
            'item_sku': 'Item',
            'movement_type': 'Movement Type',
            'quantity': 'Quantity',
            'lot_number': 'Lot Number',
            'expiry_date': 'Expiry Date',
            'note': 'Notes',
        }
        
        help_texts = {
            'item_sku': 'Select the item being moved',
            'movement_type': 'Select whether this is stock in or stock out',
            'quantity': 'Enter the quantity being moved (must be greater than 0)',
            'lot_number': 'Lot or batch number for traceability (optional, max 64 characters)',
            'expiry_date': 'Expiration date for the lot (optional, required if lot number is provided)',
            'note': 'Additional information about this movement item (optional, max 500 characters)',
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom logic"""
        # Extract stock_movement_id from kwargs if provided
        self.stock_movement_id = kwargs.pop('stock_movement_id', None)
        
        super().__init__(*args, **kwargs)
        
        # Limit item choices to active items only
        self.fields['item_sku'].queryset = ItemSKU.objects.filter(status=ItemSKU.Status.ACTIVE)
        
        # Set default movement type to IN for new items
        if not self.instance.pk:
            self.fields['movement_type'].initial = StockMovementItem.MovementType.IN
        
        # Set stock_movement initial value if provided
        if self.stock_movement_id and not self.instance.pk:
            self.fields['stock_movement'].initial = self.stock_movement_id
        
        # Make expiry_date optional by default
        self.fields['expiry_date'].required = False
        self.fields['lot_number'].required = False
    
    def clean(self):
        """Validate form data with business rules"""
        cleaned_data = super().clean()
        lot_number = cleaned_data.get('lot_number')
        expiry_date = cleaned_data.get('expiry_date')
        quantity = cleaned_data.get('quantity')
        
        # If lot number is provided, expiry date should be provided for certain item types
        if lot_number and not expiry_date:
            # You can add logic here to require expiry date for certain items
            pass
        
        # Validate quantity is positive
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError({
                'quantity': 'Quantity must be greater than 0'
            })
        
        return cleaned_data
    
    def clean_lot_number(self):
        """Validate and normalize lot number"""
        lot_number = self.cleaned_data.get('lot_number')
        if lot_number:
            # Strip whitespace and normalize
            lot_number = lot_number.strip()
            if len(lot_number) == 0:
                lot_number = None
        return lot_number
    
    def clean_note(self):
        """Validate and normalize note field"""
        note = self.cleaned_data.get('note')
        if note:
            # Strip whitespace and normalize
            note = note.strip()
            if len(note) == 0:
                note = None
        return note
