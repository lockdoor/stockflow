"""
Production Process Forms

Forms for creating and editing production processes with validation.
"""

from django import forms
from django.core.exceptions import ValidationError
from production.models.production_process import ProductionProcess
from production.models.production_result import ProductionResult
from production.models.production_loss import ProductionLoss


class ProductionProcessForm(forms.ModelForm):
    """Form for creating and editing production processes"""
    
    class Meta:
        model = ProductionProcess
        fields = [
            'production_order',
            'process_name',
            'note',
            'started_at',
            'finished_at',
        ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'finished_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)
        
        if self.production_order:
            self.fields['production_order'].initial = self.production_order
            self.fields['production_order'].widget = forms.HiddenInput()


class ProductionResultForm(forms.ModelForm):
    """Form for adding production results"""
    
    class Meta:
        model = ProductionResult
        fields = ['production_process', 'item_sku', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.production_process = kwargs.pop('production_process', None)
        super().__init__(*args, **kwargs)
        
        if self.production_process:
            self.fields['production_process'].initial = self.production_process
            self.fields['production_process'].widget = forms.HiddenInput()

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        return quantity


class ProductionLossForm(forms.ModelForm):
    """Form for adding production losses"""
    
    class Meta:
        model = ProductionLoss
        fields = ['production_process', 'item_sku', 'quantity', 'reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'reason': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.production_process = kwargs.pop('production_process', None)
        super().__init__(*args, **kwargs)
        
        if self.production_process:
            self.fields['production_process'].initial = self.production_process
            self.fields['production_process'].widget = forms.HiddenInput()

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        return quantity


class ProductionProcessUnifiedForm(forms.ModelForm):
    """Unified form for production process with results and losses"""
    
    class Meta:
        model = ProductionProcess
        fields = [
            'process_name',
            'note',
            'started_at',
            'finished_at',
        ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'finished_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)
        
        if self.production_order:
            # Set production_order for the instance
            if self.instance and not self.instance.pk:
                self.instance.production_order = self.production_order
