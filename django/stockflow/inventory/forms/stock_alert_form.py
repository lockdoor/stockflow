"""
Stock Alert Form

Form for creating and editing stock alerts with validation and clean UI.
Includes widgets for selecting items, warehouses, and setting thresholds.

Author: StockFlow Team
Created: 2025
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from inventory.models.stock_alert import StockAlert
from inventory.models.warehouse import Warehouse
from catalog.models import ItemSKU


class StockAlertForm(forms.ModelForm):
    """Form for creating and editing stock alerts"""
    
    class Meta:
        model = StockAlert
        fields = [
            'item_sku',
            'warehouse',
            'minimum_threshold',
            'critical_threshold',
            'is_enabled',
            'note',
        ]
        widgets = {
            'item_sku': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select an item...'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select a warehouse...'
            }),
            'minimum_threshold': forms.NumberInput(attrs={
                'placeholder': 'Enter minimum stock level (e.g., 100.00)',
                'step': '0.01',
                'min': '0',
                'class': 'form-control'
            }),
            'critical_threshold': forms.NumberInput(attrs={
                'placeholder': 'Enter critical stock level (e.g., 50.00)',
                'step': '0.01',
                'min': '0',
                'class': 'form-control'
            }),
            'is_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Additional notes about this alert configuration (optional)',
                'rows': 3,
                'maxlength': '1000',
                'class': 'form-control'
            }),
        }
        
        labels = {
            'item_sku': 'Item',
            'warehouse': 'Warehouse',
            'minimum_threshold': 'Minimum Threshold',
            'critical_threshold': 'Critical Threshold',
            'is_enabled': 'Enable Alert',
            'note': 'Notes',
        }
        
        help_texts = {
            'item_sku': 'Select the item for which to set up stock alerts',
            'warehouse': 'Select the warehouse where this alert applies',
            'minimum_threshold': 'Stock level that triggers a warning alert',
            'critical_threshold': 'Stock level that triggers an urgent alert (must be ≤ minimum threshold)',
            'is_enabled': 'Check to enable this stock alert',
            'note': 'Optional additional information about this alert configuration',
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with filtered querysets"""
        super().__init__(*args, **kwargs)
        
        # Filter active items and warehouses only
        self.fields['item_sku'].queryset = ItemSKU.objects.filter(
            status='ACTIVE'
        ).select_related('category').order_by('sku_code')
        
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Set required fields
        self.fields['item_sku'].required = True
        self.fields['warehouse'].required = True
        self.fields['minimum_threshold'].required = True
        self.fields['critical_threshold'].required = True
        
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            if field_name not in ['is_enabled']:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'

    def clean_minimum_threshold(self):
        """Validate minimum threshold"""
        minimum_threshold = self.cleaned_data.get('minimum_threshold')
        
        if minimum_threshold is not None:
            if minimum_threshold < Decimal('0'):
                raise ValidationError('Minimum threshold cannot be negative.')
                
        return minimum_threshold

    def clean_critical_threshold(self):
        """Validate critical threshold"""
        critical_threshold = self.cleaned_data.get('critical_threshold')
        
        if critical_threshold is not None:
            if critical_threshold < Decimal('0'):
                raise ValidationError('Critical threshold cannot be negative.')
                
        return critical_threshold

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        minimum_threshold = cleaned_data.get('minimum_threshold')
        critical_threshold = cleaned_data.get('critical_threshold')
        item_sku = cleaned_data.get('item_sku')
        warehouse = cleaned_data.get('warehouse')
        
        # Validate that critical threshold is <= minimum threshold
        if minimum_threshold is not None and critical_threshold is not None:
            if critical_threshold > minimum_threshold:
                raise ValidationError({
                    'critical_threshold': 'Critical threshold must be less than or equal to minimum threshold.'
                })
        
        # Check for duplicate item-warehouse combination (only for new records)
        if item_sku and warehouse and not self.instance.pk:
            existing_alert = StockAlert.objects.filter(
                item_sku=item_sku,
                warehouse=warehouse
            ).first()
            
            if existing_alert:
                raise ValidationError({
                    '__all__': f'A stock alert for {item_sku.sku_code} in {warehouse.name} already exists.'
                })
        
        return cleaned_data

    def save(self, commit=True, user=None):
        """Save the stock alert with proper audit fields"""
        stock_alert = super().save(commit=False)
        
        if user:
            if not stock_alert.pk:  # New record
                stock_alert.created_by = user
            stock_alert.updated_by = user
        
        if commit:
            stock_alert.save()
            
        return stock_alert


class StockAlertSearchForm(forms.Form):
    """Form for searching and filtering stock alerts"""
    
    item_sku = forms.ModelChoiceField(
        queryset=ItemSKU.objects.filter(status='ACTIVE').order_by('sku_code'),
        required=False,
        empty_label="All Items",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Warehouses",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_enabled = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Enabled'),
            ('false', 'Disabled'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by item code or warehouse name...',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        """Initialize search form"""
        super().__init__(*args, **kwargs)
        
        # Set labels
        self.fields['item_sku'].label = 'Item'
        self.fields['warehouse'].label = 'Warehouse'
        self.fields['is_enabled'].label = 'Status'
        self.fields['search'].label = 'Search'


class BulkStockAlertForm(forms.Form):
    """Form for bulk operations on stock alerts"""
    
    ACTION_CHOICES = [
        ('enable', 'Enable Selected Alerts'),
        ('disable', 'Disable Selected Alerts'),
        ('delete', 'Delete Selected Alerts'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    selected_alerts = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_selected_alerts(self):
        """Validate selected alert IDs"""
        selected_alerts = self.cleaned_data.get('selected_alerts', '')
        
        if not selected_alerts:
            raise ValidationError('No alerts selected.')
        
        try:
            alert_ids = [int(id_str) for id_str in selected_alerts.split(',') if id_str]
            if not alert_ids:
                raise ValidationError('No valid alert IDs provided.')
            return alert_ids
        except ValueError:
            raise ValidationError('Invalid alert IDs provided.')
