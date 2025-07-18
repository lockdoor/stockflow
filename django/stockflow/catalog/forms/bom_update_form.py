from django import forms
from catalog.models.bom import BOM


class BOMUpdateForm(forms.ModelForm):
    """
    Form for updating BOM entries.
    Only allows editing of quantity field - parent_sku and component_sku cannot be changed.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make parent_sku and component_sku read-only if instance exists
        if self.instance and self.instance.pk:
            self.fields['parent_sku'].disabled = True
            self.fields['component_sku'].disabled = True
            
            # Add help text to clarify what can be edited
            self.fields['quantity'].help_text = 'You can only change the quantity. Parent and component cannot be modified.'
            
            # Update labels to show read-only status
            self.fields['parent_sku'].label = 'Parent Item (Read-only)'
            self.fields['component_sku'].label = 'Component Item (Read-only)'
    
    class Meta:
        model = BOM
        fields = ['parent_sku', 'component_sku', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'parent_sku': forms.TextInput(attrs={'readonly': True, 'class': 'read-only'}),
            'component_sku': forms.TextInput(attrs={'readonly': True, 'class': 'read-only'}),
        }
        labels = {
            'parent_sku': 'Parent Item',
            'component_sku': 'Component Item',
            'quantity': 'Quantity',
        }
    
    def clean_quantity(self):
        """
        Validate quantity is positive and has max 2 decimal places.
        """
        quantity = self.cleaned_data.get('quantity')
        
        if quantity is not None:
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than zero.")
                
            # Check decimal places (max 2)
            decimal_str = str(quantity)
            if '.' in decimal_str and len(decimal_str.split('.')[1]) > 2:
                raise forms.ValidationError("Quantity cannot have more than 2 decimal places.")
        
        return quantity
    
    def clean(self):
        """
        Ensure parent_sku and component_sku are not modified for existing instances.
        For existing instances, we rely on disabled fields to prevent changes.
        This method serves as additional validation layer.
        """
        cleaned_data = super().clean()
        
        # For existing instances, ensure the cleaned data matches the instance
        # (disabled fields should preserve original values)
        if self.instance and self.instance.pk:
            # Django automatically preserves disabled field values, 
            # so we just need to validate they match the instance
            cleaned_data['parent_sku'] = self.instance.parent_sku
            cleaned_data['component_sku'] = self.instance.component_sku
        
        return cleaned_data
